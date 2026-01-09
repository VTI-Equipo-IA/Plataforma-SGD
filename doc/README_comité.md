# 🧠 Comité PMG Automatizado

**Versión institucional de generación y mantenimiento de planes de mejora (PMG) para organismos públicos chilenos.**
El sistema utiliza modelos de lenguaje (LLM) con recuperación contextual (RAG) y prompts especializados para cada dimensión PMG:
**Procedimientos**, **Gobernanza de Datos** y **Calidad Web y Servicios Digitales**.

---

## 📂 Estructura del Proyecto

```
├── 📁 mcp/
│   └── 📁 servers/
│       ├── mcp_server_pmg.py            # Comité PMG: consolida y genera planes con hitos
│       ├── mcp_server_abogado.py        # Agente legal: revisión de cumplimiento normativo
│       ├── mcp_server_desarrollador.py  # Agente técnico: factibilidad y desarrollo TI
│       ├── mcp_server_implementador.py  # Agente operativo: costo, recursos y factibilidad
│       └── mcp_server_secretario.py     # Agente de síntesis: registra consenso y acuerdos
│
├── 📁 indices/
│   ├── roadmap_mgde.json                # Mapa de actividades por subdimensión y nivel de madurez
│   ├── cpat_procedimiento.json          # Actividades obligatorias por estándar CPAT (Procedimientos)
│   ├── pmg_index/                       # Índice FAISS (RAG) del Comité PMG
│   └── gobernanza_index/ ...            # Índice RAG por dimensión
│
├── 📁 Main_excel/
│   ├── main_procedimiento_mcp_parallel.py
│   ├── main_gobernanza_mcp_parallel.py
│   └── main_calidad_web_mcp_parallel.py
│
├── 📁 Main_app/
│   ├── main_app_procedimiento.py
│   ├── main_app_gobernanza.py
│   └── main_app_web.py
│
├── 📁 utils/
│   ├── rag_loader.py                    # Carga de índices FAISS
│   ├── helpers_salida.py                # Formato de celdas, colores y merge
│   └── db_helpers.py                    # Conectores a BD y helpers SQL
│
├── 📄 crear_tabla_ptd.sql               # Script SQL para generar la tabla PTD en la BD
├── 📄 Hojas_de_Ruta_MGDE_detallado.docx # Fuente de roadmap MGDE usada para generar el JSON
└── 📄 README.md                         # Este documento
```

---

## 🧩 Arquitectura general

El sistema simula el comportamiento de un **comité multidisciplinario PMG**, compuesto por cinco agentes LLM especializados:

| Rol | Función principal |
|-----|--------------------|
| 🏛️ PMGServer | Coordina el debate, genera planes, define hitos y asegura cumplimiento del MGDE |
| ⚖️ Abogado | Evalúa legalidad, normativa y viabilidad jurídica |
| 🧑‍💻 Desarrollador | Evalúa factibilidad técnica y define integraciones de sistemas |
| 🧰 Implementador | Evalúa recursos, costos y capacidades institucionales |
| 🗂️ Secretario | Registra el consenso y genera versiones finales de los planes |

Cada agente opera bajo **prompts con flavor específico** según la dimensión (Gobernanza, Web o Procedimiento).

---

## 🧠 Flujo general de generación de planes

### 1️⃣ Entrada
El sistema recibe un dataset Excel o una fila de base de datos que contiene:
- `Dimensión`, `Subdimensión`, `Brecha`, `Pregunta`, `Respuesta` (nivel de madurez)
- Metadatos adicionales (`Contexto_PM`, `Plan anterior`, etc.)

### 2️⃣ Razonamiento del comité
1. **PMGServer** invoca `_rag_for()` → usa FAISS o JSON (según dimensión) para recuperar las actividades obligatorias del nivel actual y anterior.
2. Cada agente interviene (`intervention`) con observaciones según su dominio.
3. **PMGServer** consolida todas las observaciones (`consolidate_select`), redacta 3–4 hitos con prefijo `"HITO i:"`, y las acciones numeradas `"i.-"` que los cumplen.
4. Se garantiza que el plan **cierre la brecha de madurez** entre niveles.

### 3️⃣ Salida
- Plan completo en una celda Excel o registro BD con:
  - Acciones numeradas
  - Hitos intercalados y consistentes
  - Colores por bloque y estilos según dimensión

---

## 📊 Modos de ejecución

### 🧾 **Modo Excel (carpeta Main_excel)**
Procesa hojas de Excel completas (una por dimensión).

Ejemplo:
```bash
python Main_excel/main_gobernanza_mcp_parallel.py
```
Guarda el resultado en un archivo Excel con:
- Estilo por bandas de color
- Celdas combinadas por bloque
- Logs detallados en `/logs/`

---

### 🧩 **Modo App (carpeta Main_app)**
Usado en la **aplicación de mantenimiento de portafolio**.
Opera directamente sobre la BD PTD creada con `crear_tabla_ptd.sql`.

Ejemplo:
```bash
python Main_app/main_app_gobernanza.py --method "hito"
```

Funciones disponibles:
- `method="activity"` → Regenera actividad sin tocar hitos
- `method="hito"` → Regenera solo hitos del bloque
- `method="full"` → Regenera portafolio completo (hitos + actividades)

---

## 🔍 Especificaciones por dimensión

### 🏛️ Gobernanza de Datos
- **Fuente RAG:** `roadmap_mgde.json`
- **Nivel objetivo:** deducido automáticamente del campo `Nivel de Madurez`
- **Hitos:** 3–4 por plan
- **Reglas:**
  - No mencionar “ambientes de prueba” en temas legales.
  - Actividades coherentes con la subdimensión y sus hitos.
  - Claridad y relación directa entre acción y resultado.
  - Al menos una acción de documentación verificable.
  - Sin plazos o frecuencias cortas; dar flexibilidad a OAEs pequeñas.

---

### 🌐 Calidad Web y Servicios Digitales
- **Fuente RAG:** contexto mínimo (sin roadmap JSON)
- **Plan:** una sola actividad breve y directa (3 líneas máx.)
- **Hito:** afirmación derivada de la pregunta o brecha.
- **Reglas:**
  - No explicar el propósito (“para asegurar que…”).
  - Actividad minimalista centrada en la acción.
  - Hito consecuencia directa del cumplimiento.

---

### 🧾 Procedimientos Administrativos
- **Fuente RAG:** `cpat_procedimiento.json`
- **Objetivo:** “Mejorar trazabilidad de procedimientos con registros simples y verificables”.
- **Reglas:**
  - Favorecer automatización e integración de servicios.
  - Capacitación solo para equipos TI.
  - Actividad final debe cerrar la brecha.
  - Ponderación mayor del agente Desarrollador.

---

## 🎨 Estilo de salida (Excel)
Los archivos procesados mantienen un formato visual uniforme:

| Tipo de fila | Color |
|---------------|--------|
| Encabezado | `#BDD7EE` |
| Bloque azul común | `#DDEBF7` |
| Hito azul | `#B4C6E7` |
| Bloque verde común | `#E2F0D9` |
| Hito verde | `#C6E0B4` |

---

## ⚙️ Configuración y entorno

### Variables necesarias
| Variable | Descripción |
|-----------|--------------|
| `OPENAI_API_KEY` | Clave API de OpenAI |
| `RAG_EMB_MODEL` | Modelo de embeddings (por defecto `text-embedding-3-small`) |
| `RAG_INDEX` | Carpeta base de los índices FAISS (por dimensión) |

### Dependencias principales
```
langchain
langchain_openai
PyPDF2
openpyxl
pandas
faiss-cpu
python-docx
```

---

## 🧩 Ejemplo de ejecución (Excel)

```bash
python Main_excel/main_procedimiento_mcp_parallel.py
```

📤 Salida:
`output/Salida_Procedimiento.xlsx`
📜 Logs detallados:
`logs_procedimiento/fila_i.txt`

---

## 🧩 Ejemplo de ejecución (App)

```bash
python Main_app/main_app_gobernanza.py --method "full"
```

📤 Resultado:
Actualiza directamente los campos `Nombre_Actividad_Hito` y `Hitos` en la BD PTD.
Guarda conversación del comité en `logs_app/`.

---

## 🧱 Créditos y propósito

El sistema fue diseñado para:
- Estandarizar la redacción de planes PMG.
- Alinear las acciones al MGDE y CPAT.
- Acelerar la mejora institucional en OAEs pequeñas y medianas.

---