# 📝 Gestión de Prompts - Agente Maestro

## Descripción

Nueva vista independiente para gestionar y versionar el SuperPrompt del Agente Maestro. Permite editar, guardar versiones y restaurar a estados anteriores del prompt.

## Acceso

La vista está disponible en una ruta separada de la gestión de planes:

```
http://localhost:5000/prompts/
```

O desde cualquier navegador en tu red local usando la IP del servidor.

## Funcionalidades

### 1. ✏️ Editar Prompt

- **Editor de texto grande** con sintaxis monoespaciada para facilitar la lectura
- **Contador de caracteres** en tiempo real
- **Campos de metadata**:
  - `Etiqueta de versión`: (opcional) nombre para identificar la versión (ej: v1.2, v2.0-beta)
  - `Notas`: descripción breve de los cambios realizados

### 2. 💾 Guardar Nueva Versión

- Al hacer clic en **"Guardar Nueva Versión"**:
  - El contenido del editor se guarda como un **nuevo registro** en `ptd_prompts`
  - Se genera automáticamente una etiqueta de versión si no se especifica
  - La nueva versión se marca como **ACTIVA**
  - Las versiones anteriores se conservan en el historial

### 3. 📚 Ver Historial de Versiones

- Botón **"Ver Versiones"** muestra un modal con todas las versiones guardadas
- Para cada versión se muestra:
  - **ID**: identificador único en la base de datos
  - **Etiqueta**: nombre de la versión (ej: v1.0, v1.1)
  - **Fecha de creación**: cuándo se guardó
  - **Tamaño**: cantidad de caracteres
  - **Notas**: comentarios sobre los cambios
  - **Estado**: indica cuál es la versión ACTIVA (más reciente)

### 4. 👁️ Vista Previa de Versiones

- Desde el historial, haz clic en **"Ver"** para previsualizar el contenido completo
- Se abre un modal mostrando:
  - Metadata de la versión
  - Contenido completo del prompt en formato legible
  - Botón de **Restaurar** (si no es la versión activa)

### 5. ⏮️ Restaurar Versión Anterior

**Flujo de restauración:**

1. Desde el historial, selecciona la versión a restaurar
2. Haz clic en **"Restaurar"** o **"Ver"** → **"Restaurar Esta Versión"**
3. El sistema muestra una advertencia:
   ```
   ⚠️ ADVERTENCIA: Esta acción eliminará las X versiones 
   posteriores a "v1.0".
   
   ¿Estás seguro de que deseas restaurar a esta versión?
   ```
4. Si confirmas:
   - Se **eliminan permanentemente** todos los registros con ID mayor
   - La versión seleccionada se convierte en la versión ACTIVA
   - La página se recarga con el prompt restaurado

**Ejemplo:**

Si tienes versiones con IDs: 1, 2, 3, 4, 5 y restauras la ID=3:
- Se eliminan IDs 4 y 5
- La versión ID=3 queda como la más reciente

⚠️ **Nota importante**: La restauración es **irreversible** - las versiones posteriores se eliminan de la base de datos.

## Arquitectura Técnica

### Backend

**Blueprint**: `blueprints/prompts/`
- `__init__.py`: Inicialización del blueprint
- `routes.py`: Rutas y endpoints API

**Servicio**: `services/prompt_service.py`
- `get_latest_prompt()`: obtiene el prompt activo
- `get_all_prompts()`: lista todas las versiones
- `get_prompt_by_id(id)`: obtiene una versión específica
- `save_prompt(...)`: guarda nueva versión
- `delete_versions_after(id)`: restaura eliminando posteriores

**Tabla**: `ptd_prompts`
```sql
- id (SERIAL PRIMARY KEY)
- prompt (TEXT NOT NULL)
- version_label (VARCHAR)
- fuente (VARCHAR)
- notas (TEXT)
- fecha_creacion (TIMESTAMP)
- fecha_actualizacion (TIMESTAMP)
```

### Frontend

**Template**: `templates/prompts/index.html`
- Editor de texto con textarea grande
- Modales para historial y preview
- JavaScript vanilla (sin dependencias externas)
- CSS personalizado con animaciones

**Endpoints API**:

```
GET  /prompts/              → Vista principal
POST /prompts/api/save      → Guardar nueva versión
GET  /prompts/api/versions  → Listar todas las versiones
GET  /prompts/api/version/<id> → Obtener versión específica
POST /prompts/api/restore/<id> → Restaurar versión (elimina posteriores)
```

## Casos de Uso

### Caso 1: Editar y guardar cambios menores
1. Accede a `/prompts/`
2. Modifica el texto en el editor
3. En "Etiqueta de versión" escribe: `v1.1`
4. En "Notas" escribe: `Mejoras en instrucciones de formato`
5. Clic en **"Guardar Nueva Versión"**
6. ✅ Se guarda como nueva versión manteniendo la anterior

### Caso 2: Revertir cambios problemáticos
1. Editaste el prompt y la IA dejó de funcionar bien
2. Clic en **"Ver Versiones"**
3. Encuentra la versión anterior que funcionaba (ej: v1.0)
4. Clic en **"Ver"** para confirmar que es la correcta
5. Clic en **"Restaurar Esta Versión"**
6. Confirma la advertencia
7. ✅ El prompt vuelve al estado anterior funcional

### Caso 3: Experimentación con A/B testing
1. Guarda versión actual: `v2.0-production`
2. Haz cambios experimentales y guarda: `v2.1-test-A`
3. Prueba con algunos planes
4. Si no funciona: restaura a `v2.0-production`
5. Si funciona: guarda nueva versión: `v2.1-final`

## Seguridad y Mejores Prácticas

✅ **Recomendaciones:**
- Siempre escribe notas descriptivas al guardar versiones
- Usa etiquetas de versión consistentes (ej: v1.0, v1.1, v2.0)
- Previsualiza antes de restaurar para confirmar el contenido
- Haz backups periódicos de la tabla `ptd_prompts`

⚠️ **Precauciones:**
- La restauración elimina permanentemente versiones posteriores
- No hay "papelera de reciclaje" - las versiones eliminadas no se recuperan
- Asegúrate de probar cambios en ambiente de desarrollo primero

## Troubleshooting

**Problema**: No se carga la página
- Verifica que Flask esté corriendo: `python app.py`
- Verifica que el blueprint esté registrado en `app.py`

**Problema**: Error al guardar
- Verifica conexión a la base de datos
- Revisa que la tabla `ptd_prompts` exista
- Ejecuta: `python db/reset_and_seed_prompts.py`

**Problema**: Versiones no aparecen
- Verifica que haya al menos un registro en `ptd_prompts`
- Revisa la consola del navegador (F12) para errores JavaScript

**Problema**: Restauración no funciona
- Verifica permisos DELETE en la tabla `ptd_prompts`
- Revisa logs del servidor Flask