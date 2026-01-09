"""
Servicio para regeneración de portafolio PTD usando scripts del Agente Maestro.
Ejecuta scripts de Python en subprocess y monitorea su progreso.
"""
import subprocess
import os
import sys
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime

# Estado global de las tareas de regeneración
_regeneration_tasks: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


class RegenerationTask:
    """Representa una tarea de regeneración en curso."""
    
    def __init__(self, task_id: str, script_name: str, args: list = None):
        self.task_id = task_id
        self.script_name = script_name
        self.args = args or []
        self.status = "pending"  # pending, running, completed, failed
        self.progress = 0  # 0-100
        self.message = "Iniciando regeneración..."
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
    """Obtiene el estado de una tarea de regeneración."""
    with _lock:
        task = _regeneration_tasks.get(task_id)
        return task.to_dict() if task else None


def _run_script_thread(task: RegenerationTask, script_path: str, cwd: str):
    """Ejecuta el script en un hilo separado."""
    with _lock:
        task.status = "running"
        task.started_at = datetime.now()
        task.message = "Regenerando portafolio..."
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
            errors='replace',  # Reemplaza caracteres que no se pueden encodear
        )
        
        # Leer output en tiempo real para actualizar progreso
        output_lines = []
        error_lines = []
        
        # Actualizar progreso basado en output
        with _lock:
            task.progress = 30
            task.message = "Procesando subdimensiones..."
        
        # Esperar a que termine el proceso
        stdout, stderr = task.process.communicate()
        
        output_lines = stdout.split('\n') if stdout else []
        error_lines = stderr.split('\n') if stderr else []
        
        # Verificar código de salida
        if task.process.returncode == 0:
            with _lock:
                task.status = "completed"
                task.progress = 100
                task.message = "Portafolio regenerado exitosamente"
                task.completed_at = datetime.now()
        else:
            with _lock:
                task.status = "failed"
                task.progress = 0
                task.error = f"Error en script: {stderr[:500]}"
                task.message = "Error al regenerar portafolio"
                task.completed_at = datetime.now()
                
    except Exception as e:
        with _lock:
            task.status = "failed"
            task.progress = 0
            task.error = str(e)
            task.message = f"Error inesperado: {str(e)}"
            task.completed_at = datetime.now()


def start_regeneration(
    dimension_slug: str,
    subdimension: Optional[str] = None,
    instrumento: Optional[str] = None,
    nivel_madurez: Optional[str] = None,
    full_regeneration: bool = False
) -> str:
    """
    Inicia un proceso de regeneración de portafolio.
    
    Args:
        dimension_slug: Slug de la dimensión (gobernanza-datos, calidad-web-servicios-digital, procedimiento-administrativo)
        subdimension: Nombre de la subdimensión (opcional, para regeneración individual)
        instrumento: Instrumento (opcional, para Calidad Web)
        nivel_madurez: Nivel de madurez (opcional, para Gobernanza de Datos)
        full_regeneration: Si True, regenera todo el portafolio de la dimensión
    
    Returns:
        ID de la tarea creada
    """
    # Determinar script a ejecutar
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agente maestro")
    
    script_map = {
        "gobernanza-datos": {
            "full": "main_gobernanza_datos.py",
            "single": "generar_plan_subdimension_gd.py",
        },
        "calidad-web-servicios-digital": {
            "full": "main_calidad_web.py",
            "single": "generar_plan_subdimension_cw.py",
        },
        "procedimiento-administrativo": {
            "full": "main_procedimiento_administrativo.py",
            "single": "generar_plan_subdimension_pa.py",
        },
    }
    
    if dimension_slug not in script_map:
        raise ValueError(f"Dimensión no soportada: {dimension_slug}")
    
    scripts = script_map[dimension_slug]
    
    if full_regeneration:
        script_name = scripts["full"]
        args = []
    else:
        script_name = scripts["single"]
        args = []
        
        # Construir argumentos según la dimensión
        if dimension_slug == "gobernanza-datos":
            if not subdimension or not nivel_madurez:
                raise ValueError("Se requiere subdimension y nivel_madurez para Gobernanza de Datos")
            args = [subdimension, nivel_madurez]
        elif dimension_slug == "calidad-web-servicios-digital":
            if not subdimension or not instrumento:
                raise ValueError("Se requiere subdimension e instrumento para Calidad Web")
            args = [subdimension, instrumento]
        elif dimension_slug == "procedimiento-administrativo":
            if not subdimension:
                raise ValueError("Se requiere subdimension para Procedimiento Administrativo")
            args = [subdimension]
    
    script_path = os.path.join(base_path, script_name)
    
    # Verificar que el script existe
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script no encontrado: {script_path}")
    
    # Crear tarea
    task_id = f"{dimension_slug}_{int(time.time())}"
    task = RegenerationTask(task_id, script_name, args)
    
    with _lock:
        _regeneration_tasks[task_id] = task
    
    # Iniciar hilo de ejecución
    thread = threading.Thread(
        target=_run_script_thread,
        args=(task, script_path, base_path),
        daemon=True
    )
    thread.start()
    
    return task_id


def cancel_task(task_id: str) -> bool:
    """Cancela una tarea en ejecución."""
    with _lock:
        task = _regeneration_tasks.get(task_id)
        if not task:
            return False
        
        if task.status == "running" and task.process:
            try:
                task.process.terminate()
                task.status = "failed"
                task.error = "Cancelado por el usuario"
                task.message = "Regeneración cancelada"
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
        
        for task_id, task in _regeneration_tasks.items():
            if task.completed_at:
                age = (now - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del _regeneration_tasks[task_id]
