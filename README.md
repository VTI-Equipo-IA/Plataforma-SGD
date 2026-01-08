# 🧠 Editor de Planes PTD (Flask + PostgreSQL + IA)

**Aplicación web para la gestión y regeneración inteligente de Planes de Transformación Digital**

Sistema modular basado en Flask que permite gestionar planes estratégicos de transformación digital mediante una interfaz web intuitiva, con capacidades avanzadas de regeneración mediante Inteligencia Artificial (GPT-4 y sistemas multi-agente).

> 📖 **Para usuarios finales:** Ver [MANUAL_USUARIO.md](MANUAL_USUARIO.md) o acceder vía /manual/  
> 👨‍💻 **Para desarrolladores:** Este README

---

## 📋 Tabla de Contenidos

1. [Características Principales](#-características-principales)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Stack Tecnológico](#-stack-tecnológico)
4. [Estructura del Proyecto](#%EF%B8%8F-estructura-del-proyecto)
5. [Instalación y Configuración](#%EF%B8%8F-instalación-y-configuración)
6. [Sistemas de Regeneración IA](#-sistemas-de-regeneración-ia)
7. [API y Endpoints](#-api-y-endpoints)
8. [Base de Datos](#-base-de-datos)
9. [Frontend](#-frontend)
10. [Historial de Desarrollo](#-historial-de-desarrollo)
11. [Guías de Integración](#-guías-de-integración)
12. [Solución de Problemas](#-solución-de-problemas)
13. [Equipo y Licencia](#-equipo-y-licencia)

---

## ✨ Características Principales

### Gestión de Planes
- ✅ **CRUD completo** de planes de transformación digital
- 📊 **3 dimensiones** organizadas en pestañas (Gobernanza, Calidad Web, Procedimiento)
- 🔍 **Búsqueda avanzada** multi-columna con casting de tipos ENUM
- 📑 **Paginación** y ordenamiento dinámico por columnas
- ✏️ **Edición inline** y modal con validación
- 📝 **Gestión de Prompts**: Sistema de versionado para el SuperPrompt del Agente Maestro

### Importación/Exportación
- 💾 **Exportación a Excel** por dimensión o completa

### Gestión de Prompts del Agente Maestro
- 📝 **Editor de prompts** con vista dedicada y contador de caracteres
- 💾 **Versionado automático** con etiquetas y notas de cambios
- 📚 **Historial completo** de todas las versiones guardadas
- 👁️ **Vista previa** de cualquier versión anterior
- ⏮️ **Restauración** a versiones anteriores con confirmación
- 🗄️ **Base de datos**: Tabla `ptd_prompts` con auto-actualización
- 🔄 **Integración automática**: Scripts del Agente Maestro usan la versión más reciente

### Regeneración con IA
- 🤖 **Agente Maestro**: Regeneración de subdimensiones completas usando GPT-4
- 🤝 **Comité de Agentes**: Refinamiento de planes individuales con 5 agentes especializados
- 📈 **Seguimiento en tiempo real** del progreso de regeneración
- ⚡ **Ejecución asíncrona** mediante subprocess y threading
- 🔄 **Comparación de versiones** antes/después de regeneración

### UI/UX
- 🎨 **Interfaz moderna** con componentes reutilizables
- 📱 **Responsive design** para diferentes dispositivos
- 🔒 **Encabezados sticky** con scroll horizontal
- 📏 **Densidad ajustable** de tabla
- 🔍 **Expandir/contraer** textos largos
- ⏱️ **Modales de progreso** con animaciones CSS3

---

## 🏗️ Arquitectura del Sistema

### Patrón de Diseño

El proyecto sigue una **arquitectura en capas** (Layered Architecture) con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────┐
│              PRESENTATION LAYER                  │
│   (Templates Jinja2 + JavaScript + CSS)          │
├─────────────────────────────────────────────────┤
│            APPLICATION LAYER                     │
│         (Flask Blueprints + Routes)              │
├─────────────────────────────────────────────────┤
│             BUSINESS LAYER                       │
│  (Services: Repository, Regenerator, Importer)   │
├─────────────────────────────────────────────────┤
│              DATA LAYER                          │
│     (SQLAlchemy Models + PostgreSQL)             │
└─────────────────────────────────────────────────┘
```

### Componentes Principales

#### 1. **Capa de Presentación**
- **Templates Jinja2**: Renderizado server-side con componentes reutilizables
- **JavaScript vanilla**: Interacciones del cliente (AJAX, modales, polling)
- **CSS3**: Estilos modulares con animaciones

#### 2. **Capa de Aplicación**
- **Flask Blueprints**: Modularización por funcionalidad (`/planes`, `/prompts`, `/config`)
- **Routes**: Manejo de peticiones HTTP y respuestas JSON/HTML
- **Forms**: Validación de datos con WTForms (si aplica)

#### 3. **Capa de Negocio**
- **Repository Pattern**: Abstracción de acceso a datos
- **Service Layer**: Lógica de negocio (importación, regeneración, validación)
- **External AI Bridge**: Puente a servicios de IA externos

#### 4. **Capa de Datos**
- **SQLAlchemy ORM**: Mapeo objeto-relacional
- **PostgreSQL**: Base de datos relacional
- **Reflexión dinámica**: Carga de esquema en tiempo de ejecución

### Flujo de Datos

#### Lectura de Planes
```
Usuario → Browser → Flask Route → Repository Service → SQLAlchemy → PostgreSQL
                                                                      ↓
Usuario ← Browser ← Jinja2 Template ← Python Dict ← SQLAlchemy Result
```

#### Regeneración con IA
```
Usuario → 🤖 Button Click → JavaScript → AJAX POST → Flask Route
                                                         ↓
                                                  Regenerator Service
                                                         ↓
                                              subprocess.Popen (Python script)
                                                         ↓
                                              LangChain + GPT-4 / MCP Agents
                                                         ↓
                                              PostgreSQL (UPDATE)
                                                         ↓
JavaScript Polling ← GET /status ← Flask Route ← Task Registry
         ↓
Modal Progress Bar Update
```

---

## 🛠️ Stack Tecnológico

### Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.10+ | Lenguaje principal |
| **Flask** | 3.0.3 | Framework web |
| **SQLAlchemy** | 2.0+ | ORM para PostgreSQL |
| **psycopg2-binary** | 2.9+ | Adaptador PostgreSQL |
| **WTForms** | 3.0+ | Validación de formularios |
| **Flask-CSRF** | 0.9.2 | Protección CSRF (con @csrf.exempt para API) |
| **cryptography** | - | Cifrado Fernet para API keys |
| **openpyxl** | 3.1+ | Lectura de archivos Excel |
| **python-dotenv** | 1.0+ | Gestión de variables de entorno |

### Frontend

| Tecnología | Propósito |
|------------|-----------|
| **HTML5** | Estructura semántica |
| **CSS3** | Estilos y animaciones |
| **JavaScript (Vanilla)** | Interactividad del cliente |
| **Jinja2** | Templating server-side |
| **Fetch API** | Peticiones AJAX |

### Inteligencia Artificial

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **OpenAI API** | - | GPT-4o para Agente Maestro |
| **LangChain** | 0.1+ | Framework para aplicaciones LLM |
| **langchain-openai** | - | Integración OpenAI con LangChain |
| **MCP (Model Context Protocol)** | - | Sistema multi-agente para Comité |

### Base de Datos

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **PostgreSQL** | 13+ | Base de datos relacional |
| **pgAdmin** | - | Administración de BD (opcional) |

### Herramientas de Desarrollo

| Herramienta | Propósito |
|-------------|-----------|
| **Git** | Control de versiones |
| **VS Code** | IDE principal |
| **PowerShell / Bash** | Terminal |
| **Virtual Environment** | Aislamiento de dependencias |

---

## �️ Estructura del proyecto
```
editor-planes/
├─ app.py                      # App Flask y rutas generales
├─ blueprints/
│  ├─ planes/
│  │  ├─ __init__.py          # Blueprint /planes
│  │  ├─ routes.py            # Listado, CRUD, importación
│  │  ├─ forms.py
│  │  └─ tables.py            # Helpers de tabla/labels/paginación
│  └─ prompts/
│     ├─ __init__.py          # Blueprint /prompts
│     └─ routes.py            # API de gestión de prompts
├─ config/
│  ├─ settings.py             # Configuración Flask
│  └─ security.py             # Seguridad/CSRF/Fernet
├─ extensions/
│  ├─ db.py                   # SQLAlchemy
│  └─ csrf.py
├─ models/
│  ├─ plan_dynamic.py         # Reflexión dinámica de `ptd_planes`
│  └─ app_config.py
├─ services/
│  ├─ repository.py           # Consultas y CRUD (búsqueda/orden/paginación)
│  ├─ importer.py             # Importar Excel (upsert)
│  ├─ external_ai_bridge.py   # Puente a modelos IA
│  ├─ prompt_service.py       # CRUD para gestión de prompts
│  └─ dimensions.py           # Definiciones de dimensiones
├─ static/
│  ├─ css/styles.css
│  └─ js/ui.js
├─ templates/
│  ├─ layout.html
│  ├─ planes/
│  ├─ prompts/
│  │  └─ index.html           # Vista de gestión de prompts
│  └─ components/
├─ db/
│  ├─ crear_tabla_ptd.sql
│  ├─ crear_tabla_prompts.sql
│  ├─ reset_and_seed_prompts.py
│  └─ ejecutar_scripts_sql.py
├─ .env.example
├─ README.md
└─ CHANGELOG.md
```

## ⚙️ Instalación y Configuración

### Requisitos Previos

- **Python** 3.10 o superior
- **PostgreSQL** 13 o superior
- **pip** (gestor de paquetes de Python)
- **Git** (para clonar el repositorio)
- **OpenAI API Key** (para funcionalidades de IA)

### Paso 1: Crear Entorno Virtual

#### Windows (PowerShell)
```powershell
python -m venv editor
.\editor\Scripts\Activate.ps1
```

#### Linux/macOS
```bash
python3 -m venv editor
source editor/bin/activate
```

### Paso 2: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales** (ver `requirements.txt` completo):
```
Flask>=3.0.0
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
cryptography
WTForms
langchain>=0.1.0
langchain-openai
openai
```

### Paso 3: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# ========================================
# FLASK CONFIGURATION
# ========================================
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu_clave_secreta_super_segura_cambiar_en_produccion

# ========================================
# DATABASE CONFIGURATION
# ========================================
POSTGRES_HOST=tu_host
POSTGRES_PORT=tu_puerto
POSTGRES_DB=tu_nombre_base_datos
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password

# O usa la URI completa:
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://usuario:password@host:5432/database

# ========================================
# SECURITY
# ========================================
# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_SECRET=tu_clave_fernet_generada

# ========================================
# OPENAI API (Agente Maestro)
# ========================================
OPENAI_API_KEY=sk-tu-api-key-de-openai
AI_PROVIDER=openai
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1000

# ========================================
# COMITÉ DE AGENTES (MCP) - Opcional
# ========================================
GOB_DB_ROUNDS=3  # Número de rondas de debate para Gobernanza

# ========================================
# APPLICATION SETTINGS
# ========================================
MAX_CONTENT_LENGTH=20971520  # 20 MB límite de upload
PAGE_SIZE=25                  # Filas por página
```

> 💡 **Tip:** Nunca subas el archivo `.env` a Git. Usa `.env.example` como plantilla.

### Paso 4: Crear la Base de Datos

#### Opción A: Script automatizado
```bash
cd db
python ejecutar_scripts_sql.py
```

#### Opción B: Manualmente con psql
```bash
psql -h tu_host -U tu_usuario -d postgres
CREATE DATABASE tu_nombre_base_datos;
\c tu_nombre_base_datos
\i db/crear_tabla_ptd.sql
\q
```

La tabla `ptd_planes` contiene estos campos:
- `id` (SERIAL PRIMARY KEY)
- `Dimension` (TEXT) - Dimensión del plan
- `Subdimension` (TEXT) - Subdimensión específica
- `Instrumento` (TEXT) - Herramienta o documento
- `Nivel_de_madurez` (ENUM) - Estado de implementación
- `Hito` (TEXT) - Objetivo a alcanzar
- `Actividad` (TEXT) - Tarea concreta
- Timestamps: `created_at`, `updated_at`

### Paso 5: Ejecutar la Aplicación

#### Modo Desarrollo
```bash
flask run
# o
python app.py
```

#### Modo Producción (con Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Abrir navegador en: **http://127.0.0.1:5000**

### Paso 7: Verificar Instalación

✅ **Checklist de verificación:**

1. **Base de datos conectada:**
   - Ve a http://127.0.0.1:5000/planes/gobernanza
   - Deberías ver la tabla (vacía o con datos)

2. **Importación funciona:**
   - Haz clic en "📥 Importar"
   - Selecciona un archivo Excel válido
   - Verifica que los datos se carguen

3. **Regeneración IA disponible:**
   - Haz clic en "🤖 Regenerar con IA"
   - Si aparece el modal, la configuración es correcta

4. **No hay errores en consola:**
   - Abre DevTools (F12)
   - Pestaña "Console" no debe mostrar errores JavaScript

---

## 🤖 Sistemas de Regeneración IA

La aplicación implementa **dos sistemas complementarios** de regeneración mediante IA:

### Sistema 1: Agente Maestro (GPT-4)

**Arquitectura:**
```
Flask Route (/regenerate-plan)
    ↓
services/plan_regenerator.py
    ↓
subprocess.Popen([sys.executable, script_path])
    ↓
agente maestro/generar_plan_subdimension_*.py
    ↓
LangChain + ChatOpenAI (GPT-4o, temp=0.3)
    ↓
PostgreSQL UPDATE (subdimensión completa)
```

**Características:**
- ✅ Regenera **subdimensiones completas**
- ✅ Usa **un solo agente potente** (GPT-4o)
- ✅ **Rápido** (2-5 minutos por subdimensión)
- ✅ Parámetros: `dimension`, `subdimension`, `instrumento`, `nivel_madurez`

**Scripts por dimensión:**
- `generar_plan_subdimension_gd.py` → Gobernanza de Datos
- `generar_plan_subdimension_cw.py` → Calidad Web
- `generar_plan_subdimension_pa.py` → Procedimiento Administrativo

**Integración con Gestión de Prompts:**
Todos los scripts del Agente Maestro ahora cargan el SuperPrompt desde la base de datos:

```python
def cargar_superprompt():
    """Carga el SuperPrompt desde la base de datos (versión más reciente)"""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT prompt 
            FROM ptd_prompts 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except Exception as e:
        # Fallback al archivo .md si hay error
        with open('SuperPrompt_AgenteMaestro_PTD.md', 'r') as f:
            return f.read()
```

Esto significa que:
- ✅ Cualquier cambio en `/prompts/` se refleja inmediatamente en regeneraciones
- ✅ No necesitas editar archivos `.md` manualmente
- ✅ Versionado completo de cambios en el prompt
- ✅ Rollback instantáneo si una versión causa problemas

**Flujo de ejecución:**

1. Usuario hace clic en 🤖
2. Modal captura parámetros desde `data-*` attributes
3. JavaScript envía POST a `/planes/<dim>/regenerate-plan`
4. Backend crea `RegenerationTask` con UUID
5. Thread secundario ejecuta script Python con `subprocess`
6. JavaScript hace polling cada 2.5s a `/regeneration-status/<task_id>`
7. Script actualiza BD y termina
8. Task marca status como `completed`
9. Modal muestra "✅ Completado"
10. Usuario recarga para ver cambios

**Código clave:**

```python
# services/plan_regenerator.py
def start_regeneration(dimension_slug, subdimension, instrumento, nivel_madurez, full_regeneration=False):
    task = RegenerationTask(
        dimension_slug=dimension_slug,
        subdimension=subdimension,
        # ...
    )
    thread = threading.Thread(target=_run_script_thread, args=(task,))
    thread.daemon = True
    thread.start()
    return task.task_id
```

### Sistema 2: Comité de Agentes (MCP)

**Arquitectura:**
```
Flask Route (/regenerate-plan-comite)
    ↓
services/comite_regenerator.py
    ↓
subprocess.Popen([sys.executable, script_path, row_id, mode])
    ↓
comite/scripts/*_db_row_comite.py
    ↓
MCP Agents (5 especializados):
  - PMG (Project Manager)
  - Abogado (Legal)
  - Desarrollador (Technical)
  - Implementador (Execution)
  - Secretario (Documentation)
    ↓
PostgreSQL UPDATE (fila específica)
```

**Características:**
- ✅ Refina **planes individuales** (por `row_id`)
- ✅ Usa **5 agentes especializados** que debaten
- ✅ **Más lento** pero **más detallado** (5-8 minutos)
- ✅ Modos: `regen-planes-only`, `regen-hitos-only`, o ambos

**Scripts por dimensión:**
- `gob_db_row_comite.py` → Gobernanza (requiere `--mode`)
- `web_db_row_comite.py` → Calidad Web (requiere tipo: `hito` o `activity`)
- `proc_db_row_comite.py` → Procedimiento (requiere tipo + rounds)

**Ejemplo de comandos:**

```bash
# Gobernanza
python comite/scripts/gob_db_row_comite.py 123 --mode regen-planes-only

# Calidad Web
python comite/scripts/web_db_row_comite.py 456 hito 3

# Procedimiento
python comite/scripts/proc_db_row_comite.py 789 activity 3
```

**Infraestructura completa pero scripts pendientes:**

> ⚠️ **Estado actual:** Backend, endpoints y JavaScript 100% implementados.  
> El sistema está listo para funcionar apenas se copie la carpeta `comite/` al proyecto.

**Documentación del sistema:**
- Ver: [doc/README_comité.md](doc/README_comité.md) - Documentación del Sistema Comité de Agentes

---

## 📡 API y Endpoints

### Rutas Principales

#### Planes - Visualización

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/planes/<dimension>` | Lista planes de una dimensión con paginación |
| GET | `/planes/<dimension>?search=texto` | Búsqueda multi-columna |
| GET | `/planes/<dimension>?sort=columna&order=asc` | Ordenamiento |

**Parámetros de query:**
- `search`: Texto a buscar (multi-columna con casting)
- `sort`: Columna por la cual ordenar
- `order`: `asc` o `desc`
- `page`: Número de página (default: 1)
- `per_page`: Filas por página (default: 25)

#### Planes - CRUD

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/planes/<dimension>/create` | Crea nuevo plan |
| GET | `/planes/<dimension>/edit/<id>` | Obtiene plan para editar |
| POST | `/planes/<dimension>/update/<id>` | Actualiza plan existente |
| POST | `/planes/<dimension>/delete/<id>` | Elimina plan |

**Request body (JSON):**
```json
{
  "subdimension": "Estrategia y Gobierno del Dato",
  "instrumento": "Política de Datos Abiertos",
  "nivel_madurez": "Definido",
  "hito": "Implementar catálogo de datos",
  "actividad": "Desarrollar plataforma web"
}
```

#### Importar/Exportar

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/planes/import` | Importa desde Excel (multipart/form-data) |
| GET | `/planes/<dimension>/export` | Exporta dimensión a JSON |
| GET | `/planes/export-all` | Exporta todas las dimensiones |

**Importar Excel:**
```bash
curl -X POST http://localhost:5000/planes/import \
  -F "file=@planes.xlsx"
```

#### Regeneración - Agente Maestro

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/planes/<dim>/regenerate-plan` | Regenera subdimensión específica |
| POST | `/planes/<dim>/regenerate-full` | Regenera dimensión completa |
| GET | `/planes/<dim>/regeneration-status/<task_id>` | Consulta progreso |
| POST | `/planes/<dim>/cancel-regeneration/<task_id>` | Cancela tarea |

**Request body:**
```json
{
  "subdimension": "Estrategia y Gobierno del Dato",
  "instrumento": "Política de Datos Abiertos",
  "nivel_madurez": "Definido"
}
```

**Response:**
```json
{
  "success": true,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Regeneración iniciada"
}
```

**Polling status:**
```json
{
  "status": "running",  // "pending" | "running" | "completed" | "error" | "cancelled"
  "progress": 65,       // 0-100
  "message": "Generando hitos y actividades...",
  "started_at": "2025-11-11T10:30:00",
  "logs": ["Log line 1", "Log line 2"]
}
```

#### Regeneración - Comité

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/planes/<dim>/regenerate-plan-comite` | Refina plan por row_id |
| GET | `/planes/<dim>/comite-status/<task_id>` | Consulta progreso |
| POST | `/planes/<dim>/cancel-comite/<task_id>` | Cancela tarea |

**Request body:**
```json
{
  "row_id": 123,
  "mode": "regen-planes-only"  // o "regen-hitos-only" o "all"
}
```

#### Gestión de Prompts

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/prompts/` | Vista principal de gestión |
| POST | `/prompts/api/save` | Guarda nueva versión del prompt |
| GET | `/prompts/api/versions` | Lista todas las versiones |
| GET | `/prompts/api/version/<id>` | Obtiene versión específica |
| POST | `/prompts/api/restore/<id>` | Restaura versión (elimina posteriores) |
| DELETE | `/prompts/api/delete/<id>` | Elimina versión específica |

**Request body (save):**
```json
{
  "prompt": "Texto completo del SuperPrompt...",
  "version_label": "v2.0",
  "notas": "Mejoras en instrucciones de formato"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prompt guardado exitosamente como v2.0",
  "id": 5,
  "version_label": "v2.0"
}
```

#### Configuración

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/config` | Página de configuración |
| POST | `/config/update` | Actualiza configuración |

---

## �️ Base de Datos

### Esquema de `ptd_planes`

```sql
CREATE TYPE tipo_nivel_madurez AS ENUM (
    'Inicial',
    'Gestionado',
    'Definido',
    'Cuantitativo',
    'Optimizado'
);

CREATE TABLE ptd_planes (
    id SERIAL PRIMARY KEY,
    "Dimension" TEXT NOT NULL,
    "Subdimension" TEXT,
    "Instrumento" TEXT,
    "Nivel_de_madurez" tipo_nivel_madurez,
    "Hito" TEXT,
    "Actividad" TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dimension ON ptd_planes("Dimension");
CREATE INDEX idx_subdimension ON ptd_planes("Subdimension");
```

### Dimensiones Válidas

```python
DIMENSIONS = {
    'gobernanza': 'Gobernanza de datos',
    'calidad-web': 'Calidad web y servicios digitales',
    'procedimiento': 'Procedimiento administrativo de función específica'
}
```

### Modelo ORM (SQLAlchemy)

```python
# models/plan_dynamic.py
from extensions.db import db

class PlanDynamic:
    """Reflexión dinámica de la tabla ptd_planes"""
    
    @staticmethod
    def get_table():
        metadata = db.MetaData()
        metadata.reflect(bind=db.engine, only=['ptd_planes'])
        return metadata.tables['ptd_planes']
```

### Consultas Comunes

#### Búsqueda multi-columna con ENUM casting

```python
# services/repository.py
search_cols = [
    table.c.Subdimension,
    table.c.Instrumento,
    table.c.Hito,
    table.c.Actividad,
    cast(table.c.Nivel_de_madurez, Text)  # Cast ENUM a TEXT
]

filters = [col.ilike(f"%{search}%") for col in search_cols]
query = query.filter(or_(*filters))
```

#### Paginación

```python
total = query.count()
plans = query.offset((page - 1) * per_page).limit(per_page).all()
```

---

## 🎨 Frontend

### Estructura de Templates

```
templates/
├── layout.html                 # Base template con navbar y scripts
├── planes/
│   ├── index.html             # Vista principal de tabla
│   └── edit_modal.html        # Modal de edición
└── components/
    ├── top_toolbar.html       # Barra de herramientas superior
    ├── table_actions.html     # Botones de acción por fila
    ├── comparative_view.html  # Comparación de versiones
    └── plan_card.html         # Vista de tarjeta (alternativa)
```

### JavaScript (`static/js/ui.js`)

**Funciones principales:**

```javascript
// Agente Maestro
function regeneratePlan(dimension, subdimension, instrumento, nivelMadurez)
function regenerateFull(dimension)
function pollRegenerationStatus(dim, taskId)

// Comité
function regeneratePlanComite(rowId, mode)
function pollComiteStatus(dim, taskId)

// UI
function showRegenerationModal(title)
function updateRegenerationStatus(message, progress)
function hideRegenerationModal()
```

**Polling pattern:**

```javascript
function pollRegenerationStatus(dim, taskId) {
    const interval = setInterval(() => {
        fetch(`/planes/${dim}/regeneration-status/${taskId}`)
            .then(res => res.json())
            .then(data => {
                updateRegenerationStatus(data.message, data.progress);
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    showSuccessMessage();
                }
            });
    }, 2500);  // Poll cada 2.5 segundos
}
```

### CSS (`static/css/styles.css`)

**Características destacadas:**

- **Sticky headers**: Encabezados fijos al hacer scroll
- **Scroll horizontal**: Para tablas anchas
- **Animaciones CSS3**: fadeIn, slideUp, spin
- **Responsive**: Media queries para móviles
- **Densidad ajustable**: Clases `.compact`, `.normal`, `.comfortable`

```css
/* Encabezado sticky */
.table-container thead th {
    position: sticky;
    top: 0;
    z-index: 10;
    background: #fff;
}

/* Animación de carga */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.spinner {
    animation: spin 1s linear infinite;
}
```

---

## �️ Datos y dimensiones
La app usa una única tabla `ptd_planes`. Las pestañas filtran por el campo `Dimension` con estos valores exactos:
1. "Gobernanza de datos"
2. "Calidad web y servicios digitales"
3. "Procedimiento administrativo de función específica"

## 📦 Importar desde Excel
- Archivos `.xlsx` con hojas nombradas igual que las dimensiones.
- Desde `/planes`, botón “Importar Excel”.
- Modo upsert:
  - Con `id` → actualiza
  - Sin `id` → inserta

## 🔎 Búsqueda y orden
- Cuadro de búsqueda aplica OR sobre varias columnas visibles (ej.: Brecha, Indicador, Iniciativa, Descripcion, Subdimension, Instrumento, Tipo, Autor, Nivel_de_madurez y Dimension). Los campos no textuales se castean a texto para evitar errores con ENUM.
- Puedes ordenar haciendo clic en el encabezado de cada columna (flechas ▲/▼).

## 💡 Consejos de uso de la tabla
- Encabezados se mantienen visibles al hacer scroll vertical.
- Si hay muchas columnas, el cuadro de la tabla permite scroll horizontal.
- Los textos largos aparecen truncados a 4 líneas; usa “Ver más/Ver menos” o “Expandir texto”.
- Cambia la densidad con “Más espacio / Menos espacio”.

## 🔒 Seguridad
- CSRF habilitado
- API keys cifradas con Fernet
- Transacciones y rollback ante errores

## 🛠️ Solución de problemas
- "operator does not exist: tipo_nivel_madurez ~~* unknown": usa la versión actual (se castea a `TEXT` en la búsqueda).
- Problemas de conexión: verifica VPN, DNS y valores de `.env`. Prueba puerto 5432 con `Test-NetConnection` (Windows).

## 📚 Documentación Completa

### Para Usuarios
- 📖 **[doc/MANUAL_USUARIO.md](doc/MANUAL_USUARIO.md)** - Guía completa de uso (incluye Gestión de Prompts)

### Para Desarrolladores
- 🛠️ **[README.md](README.md)** (este archivo) - Arquitectura y referencia técnica
- 📝 **[CHANGELOG.md](CHANGELOG.md)** - Registro de cambios por versión
- 🏗️ **[doc/STACK_TECNOLOGICO.md](doc/STACK_TECNOLOGICO.md)** - Tecnologías, arquitectura y decisiones técnicas
- 📝 **[doc/PROMPTS_README.md](doc/PROMPTS_README.md)** - Sistema de gestión de prompts (200+ líneas)
- 🤖 **[doc/README_agente_maestro.md](doc/README_agente_maestro.md)** - Generación automatizada con IA
- 🤝 **[doc/README_comité.md](doc/README_comité.md)** - Sistema multi-agente MCP
- 📄 **[doc/DESARROLLO_SUPERPROMPT.md](doc/DESARROLLO_SUPERPROMPT.md)** - Desarrollo y evolución del SuperPrompt

### Esquemas SQL
- 💾 **[db/crear_tabla_ptd.sql](db/crear_tabla_ptd.sql)** - Esquema tabla ptd_planes
- 💾 **[db/crear_tabla_prompts.sql](db/crear_tabla_prompts.sql)** - Esquema tabla ptd_prompts

---

## 📜 Evolución del Sistema

**¿Cómo se construyó esta aplicación?**

El sistema ha evolucionado desde un CRUD básico hasta una plataforma completa con IA:
- ✅ **Fase 1:** Fundación (Octubre 2025) - Flask + PostgreSQL + CRUD
- ✅ **Fase 2:** Búsqueda y UX (Octubre 2025) - Problema ENUM resuelto
- ✅ **Fase 3:** Importación Excel (Octubre 2025) - Modo upsert
- ✅ **Fase 4:** Agente Maestro (Noviembre 2025) - Regeneración con GPT-4
- ✅ **Fase 5:** Sistema Comité (Noviembre 2025) - Infraestructura multi-agente MCP
- ✅ **Fase 6:** Gestión de Prompts (Noviembre 2025) - Versionado web del SuperPrompt
- ✅ Fase 6: Documentación (Noviembre 2025) - Manuales de usuario
- ✅ Fase 7: README técnico (Noviembre 2025) - Este documento

**Lecciones aprendidas, decisiones arquitectónicas y soluciones a problemas técnicos están documentadas en detalle.**

---
 

## 👥 Equipo

**VTI - Oficina de IA**  
Universidad de Chile  
Proyecto PMG - Plan de Mejoramiento a la Gestión

### Contacto
- 📧 Email: oficina.ia@uchile.cl
- 🌐 Web: [Oficina de IA](https://ia.uchile.cl/)

---

## 📄 Licencia

**Uso interno/educativo**  
Proyecto PMG - Universidad de Chile

⚠️ **Importante:**
- No distribuir credenciales de producción
- No publicar API keys
- Mantener `.env` en `.gitignore`

---

**Última actualización:** 26 de Noviembre de 2025  
**Versión:** 2.1  
**Estado:** ✅ Producción (Agente Maestro + Gestión de Prompts)
