"""
Servicio para regeneración de planes PTD usando scripts del Comité.
Ejecuta scripts de refinamiento iterativo por fila individual con sistema de agentes MCP.

NOTA PARA DESARROLLADOR:
=======================
Este servicio está LISTO para funcionar. Solo necesitas:

1. Copiar la carpeta 'comite/' completa con sus scripts en la raíz del proyecto
2. Verificar que existan estos archivos:
   - comite/scripts/gob_db_row_comite.py
   - comite/scripts/web_db_row_comite.py
   - comite/scripts/proc_db_row_comite.py
   - comite/mcp/servers/mcp_server_*.py (todos los servidores MCP)

3. Instalar dependencias del comité si son diferentes a las actuales

4. Los endpoints ya están creados en blueprints/planes/routes.py
5. Los botones ya están en la interfaz (actualmente deshabilitados)
6. El JavaScript ya está implementado en static/js/ui.js

Para habilitar los botones, ir a templates/components/top_toolbar.html y quitar 'disabled'.
"""
import subprocess
import os
import sys
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime

# Estado global de las tareas de regeneración del comité
_comite_tasks: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


class ComiteRegenerationTask:
    """Representa una tarea de regeneración del comité en curso."""
    
    def __init__(self, task_id: str, script_name: str, args: list = None):
        self.task_id = task_id
        self.script_name = script_name
        self.args = args or []
        self.status = "pending"  # pending, running, completed, failed
        self.progress = 0  # 0-100
        self.message = "Iniciando refinamiento con comité..."
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.process = None
        
    def to_dict(self) -> dict:
        """Convierte la tarea a diccionario para JSON."""
        return {
            "task_id": self.task_id,
            "script_name": self.script_name,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene el estado de una tarea de regeneración del comité."""
    with _lock:
        task = _comite_tasks.get(task_id)
        return task.to_dict() if task else None


def _run_script_thread(task: ComiteRegenerationTask, script_path: str, cwd: str):
    """Ejecuta el script del comité en un hilo separado."""
    with _lock:
        task.status = "running"
        task.started_at = datetime.now()
        task.message = "Refinando con comité de agentes..."
        task.progress = 10
    
    try:
        # Construir comando usando el Python del entorno virtual activo
        cmd = [sys.executable, script_path] + task.args
        
        # Configurar entorno para UTF-8 en Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Ejecutar script
        task.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            encoding='utf-8',
            errors='replace',
        )
        
        # Actualizar progreso
        with _lock:
            task.progress = 30
            task.message = "Procesando con agentes MCP..."
        
        # Esperar a que termine el proceso
        stdout, stderr = task.process.communicate()
        
        # Verificar código de salida
        if task.process.returncode == 0:
            with _lock:
                task.status = "completed"
                task.progress = 100
                task.message = "Plan refinado exitosamente por el comité"
                task.completed_at = datetime.now()
        else:
            with _lock:
                task.status = "failed"
                task.progress = 0
                task.error = f"Error en script: {stderr[:500]}"
                task.message = "Error al refinar plan con comité"
                task.completed_at = datetime.now()
                
    except Exception as e:
        with _lock:
            task.status = "failed"
            task.progress = 0
            task.error = str(e)
            task.message = f"Error inesperado: {str(e)}"
            task.completed_at = datetime.now()


def start_comite_regeneration(
    dimension_slug: str,
    row_id: int,
    mode: str = "regen-planes-only"
) -> str:
    """
    Inicia un proceso de regeneración con el comité.
    
    Args:
        dimension_slug: Slug de la dimensión (gobernanza-datos, calidad-web-servicios-digital, procedimiento-administrativo)
        row_id: ID de la fila a procesar
        mode: Modo de regeneración
            - Para Gobernanza: "regen-planes-only" o "regen-hitos-only"
            - Para Calidad Web: "hito" o "activity"
            - Para Procedimiento: "hito" o "activity"
    
    Returns:
        ID de la tarea creada
    """
    # Determinar script a ejecutar
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "comite", "scripts")
    
    # Verificar que la carpeta comite existe
    if not os.path.exists(base_path):
        raise FileNotFoundError(
            "La carpeta 'comite/scripts' no existe. "
            "Por favor, copia la carpeta 'comite' completa en la raíz del proyecto."
        )
    
    script_map = {
        "gobernanza-datos": "gob_db_row_comite.py",
        "calidad-web-servicios-digital": "web_db_row_comite.py",
        "procedimiento-administrativo": "proc_db_row_comite.py",
    }
    
    if dimension_slug not in script_map:
        raise ValueError(f"Dimensión no soportada: {dimension_slug}")
    
    script_name = script_map[dimension_slug]
    script_path = os.path.join(base_path, script_name)
    
    # Verificar que el script existe
    if not os.path.exists(script_path):
        raise FileNotFoundError(
            f"Script no encontrado: {script_path}\n"
            f"Asegúrate de que existe el archivo 'comite/scripts/{script_name}'"
        )
    
    # Construir argumentos según la dimensión
    args = [str(row_id)]
    
    if dimension_slug == "gobernanza-datos":
        # Gobernanza usa: row_id --mode [regen-planes-only|regen-hitos-only]
        args.extend(["--mode", mode])
    else:
        # Calidad Web y Procedimiento usan: row_id [hito|activity] [rounds]
        args.append(mode)
        args.append("3")  # número de rondas por defecto
    
    # Crear tarea
    task_id = f"comite_{dimension_slug}_{row_id}_{int(time.time())}"
    task = ComiteRegenerationTask(task_id, script_name, args)
    
    with _lock:
        _comite_tasks[task_id] = task
    
    # Iniciar hilo de ejecución
    thread = threading.Thread(
        target=_run_script_thread,
        args=(task, script_path, base_path),
        daemon=True
    )
    thread.start()
    
    return task_id


def cancel_task(task_id: str) -> bool:
    """Cancela una tarea en ejecución del comité."""
    with _lock:
        task = _comite_tasks.get(task_id)
        if not task:
            return False
        
        if task.status == "running" and task.process:
            try:
                task.process.terminate()
                task.status = "failed"
                task.error = "Cancelado por el usuario"
                task.message = "Refinamiento cancelado"
                task.completed_at = datetime.now()
                return True
            except Exception:
                return False
        
        return False


def cleanup_old_tasks(max_age_hours: int = 24):
    """Elimina tareas antiguas del registro."""
    with _lock:
        now = datetime.now()
        to_remove = []
        
        for task_id, task in _comite_tasks.items():
            if task.completed_at:
                age = (now - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del _comite_tasks[task_id]
