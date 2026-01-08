# Agente Maestro PTD - Sistema Automatizado de Generación de Planes de Transformación Digital

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue)](https://www.postgresql.org/)
[![OpenAI](https://img.shields.io/badge/openai-gpt--4o-green)](https://openai.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Sistema inteligente para automatizar la redacción de Planes de Transformación Digital (PTD) para el Programa de Mejoramiento de la Gestión (PMG) del gobierno chileno.

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Guía de Uso](#-guía-de-uso)
- [Scripts Principales](#-scripts-principales)
- [Base de Datos](#-base-de-datos)
- [SuperPrompt](#-superprompt)
- [Adaptación a Otros PMG](#-adaptación-a-otros-pmg)
- [Troubleshooting](#-troubleshooting)
- [Contribución](#-contribución)

---

## 🎯 Descripción General

### ¿Qué es el Agente Maestro PTD?

El **Agente Maestro PTD** es un sistema automatizado que genera Planes de Transformación Digital estructurados para el PMG de Transformación Digital del gobierno chileno. Procesa indicadores de diagnóstico, identifica brechas y genera planes detallados con actividades y hitos específicos.

### Objetivos del Sistema

1. **Automatización completa:** Eliminar redacción manual de planes PTD
2. **Consistencia:** Generar planes con estructura y calidad uniforme
3. **Escalabilidad:** Procesar múltiples dimensiones y subdimensiones
4. **Flexibilidad:** Permitir generación masiva o selectiva
5. **Almacenamiento persistente:** Base de datos PostgreSQL para análisis

### Dimensiones PMG Soportadas

El sistema procesa **3 dimensiones principales**:

1. **Procedimiento Administrativo de Función Específica** (6 subdimensiones)
   - Autenticación digital oficial
   - Interoperabilidad
   - Notificaciones electrónicas
   - Ingreso de solicitudes
   - Expedientes electrónicos
   - Comunicaciones oficiales

2. **Gobernanza de Datos** (12 subdimensiones × 3 niveles de madurez = 36 planes)
   - Visión Estratégica, Gobierno de Datos, Organización, etc.
   - Niveles: Insuficiente → Básico → Medio → Avanzado

3. **Calidad Web y Servicios Digitales** (22 subdimensiones × instrumentos = 40 planes)
   - 575 preguntas de checkeo agrupadas por indicador
   - 2 instrumentos de evaluación

---

## 🏗️ Arquitectura del Sistema

### Arquitectura Dual: Main Scripts + Subscripts

El sistema implementa una **arquitectura de dos niveles**:

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTE MAESTRO PTD                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐      ┌────────────────────────┐   │
│  │   MAIN SCRIPTS      │      │     SUBSCRIPTS         │   │
│  │  (Batch Processing) │      │  (Targeted Processing) │   │
│  └─────────────────────┘      └────────────────────────┘   │
│           │                              │                   │
│           ├─ main_procedimiento_administrativo.py           │
│           ├─ main_gobernanza_datos.py                       │
│           ├─ main_calidad_web.py                            │
│           │                              │                   │
│           │                    ├─ generar_plan_subdimension_pa.py
│           │                    ├─ generar_plan_subdimension_gd.py
│           │                    └─ generar_plan_subdimension_cw.py
│           │                              │                   │
│           └──────────────────────────────┘                   │
│                          │                                   │
│                    ┌─────▼─────┐                            │
│                    │SuperPrompt│                            │
│                    └─────┬─────┘                            │
│                          │                                   │
│              ┌───────────┴───────────┐                      │
│              │                       │                      │
│        ┌─────▼─────┐         ┌─────▼─────┐                │
│        │  OpenAI   │         │PostgreSQL │                │
│        │  GPT-4o   │         │  Database │                │
│        └───────────┘         └───────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Procesamiento

```
┌─────────────────┐
│  1. LECTURA     │  ← PostgreSQL (ptd_planes table)
│  Datos de DB    │
└────────┬────────┘
         │
┌────────▼────────┐
│  2. GENERACIÓN  │  ← OpenAI GPT-4o + SuperPrompt
│  Plan con LLM   │
└────────┬────────┘
         │
┌────────▼────────┐
│  3. GENERACIÓN  │  ← OpenAI GPT-4o (indicador cualitativo)
│  Indicador      │
└────────┬────────┘
         │
┌────────▼────────┐
│  4. PARSEO      │  ← Extracción de (numero, tipo, descripcion)
│  Plan a registros│
└────────┬────────┘
         │
┌────────▼────────┐
│  5. ELIMINACIÓN │  ← DELETE WHERE dimension + subdimension + autor
│  Plan antiguo   │
└────────┬────────┘
         │
┌────────▼────────┐
│  6. INSERCIÓN   │  ← INSERT nuevos registros
│  Nuevos registros│
└────────┬────────┘
         │
┌────────▼────────┐
│  7. COMMIT      │  ← Commit transacción
│  Transacción    │
└─────────────────┘
```

### Identificación Única de Planes

Cada dimensión utiliza una **clave única diferente**:

| Dimensión | Clave Única | Ejemplo |
|-----------|-------------|---------|
| **Procedimiento Administrativo** | Dimension + Subdimension + Autor | `('PA', 'Autenticación', 'Agente Maestro')` |
| **Gobernanza de Datos** | Dimension + Subdimension + Nivel + Autor | `('GD', 'Organización', 'Basico', 'Agente Maestro')` |
| **Calidad Web** | Dimension + Subdimension + Instrumento + Autor | `('CW', 'Accesibilidad web', 'Instrumento...', 'Agente Maestro')` |

---

## 💻 Tecnologías Utilizadas

### Stack Tecnológico

#### Backend y Procesamiento
- **Python 3.8+**: Lenguaje principal
- **LangChain**: Framework para LLM y agentes
- **OpenAI GPT-4o**: Modelo de lenguaje (temperature=0.3)
- **psycopg2-binary 2.9.10**: Driver PostgreSQL

#### Base de Datos
- **PostgreSQL 16-alpine**: Base de datos relacional
- **Docker**: Contenedorización de PostgreSQL
- **ENUM Types**: Validación a nivel de esquema

#### Gestión de Configuración
- **python-dotenv**: Variables de entorno
- **config.py**: Configuración centralizada

#### Dependencias Completas

Ver `requirements.txt`:
```txt
langchain-openai==0.2.12
openai==1.56.2
psycopg2-binary==2.9.10
python-dotenv==1.0.1
openpyxl==3.1.5  # Solo para scripts de migración (deprecado en mains)
```

### Infraestructura

```
┌──────────────────────────────────────────┐
│  Docker Container: postgres_ptd          │
│  ┌────────────────────────────────────┐  │
│  │  PostgreSQL 16-alpine              │  │
│  │  Puerto: 5432                      │  │
│  │  Database: ptd_db                  │  │
│  │  Volume: postgres_ptd_data         │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
                    ▲
                    │ psycopg2
                    │
┌───────────────────┴──────────────────────┐
│  Scripts Python                           │
│  ┌────────────────────────────────────┐  │
│  │  main_*.py / generar_*.py          │  │
│  │  OpenAI API (GPT-4o)               │  │
│  │  SuperPrompt                       │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 📖 Guía de Uso

### Flujo de Trabajo Recomendado

```
1. INSTALACIÓN → Configurar ambiente, DB, variables de entorno
2. MIGRACIÓN   → Cargar datos iniciales a PostgreSQL (si aplica)
3. TESTING     → Probar con subscripts (1 plan específico)
4. PRODUCCIÓN  → Ejecutar main scripts (todos los planes)
5. VALIDACIÓN  → Verificar resultados en DB
6. ITERACIÓN   → Ajustar SuperPrompt si es necesario
```

### Casos de Uso Comunes

#### Caso 1: Generar Todos los Planes de una Dimensión

**Escenario:** Primera generación o regeneración completa

```bash
# Activar ambiente virtual
.\venv\Scripts\Activate.ps1

# Ejecutar main script
python main_procedimiento_administrativo.py    # 6 planes PA
# o
python main_gobernanza_datos.py                # 36 planes GD
# o
python main_calidad_web.py                     # 40 planes CW (575 preguntas)
```

**Output esperado:**
```
Conectando a PostgreSQL...
✅ Conexión exitosa a ptd_db

Procesando subdimensión 1/6: Autenticación digital
Generando plan con LLM...
Generando indicador de resultado...
Parseando plan a registros...
Eliminando plan antiguo...
Insertando 10 nuevos registros...
✅ Plan guardado exitosamente

...

═══════════════════════════════════════════════
RESUMEN DE EJECUCIÓN
═══════════════════════════════════════════════
Total subdimensiones procesadas: 6
Planes generados: 6
Planes con errores: 0
Tiempo total: 3m 45s
```

#### Caso 2: Regenerar Un Plan Específico

**Escenario:** Corrección o testing de un plan problemático

```bash
# Procedimiento Administrativo (1 argumento)
python generar_plan_subdimension_pa.py "Autenticación digital"

# Gobernanza de Datos (2 argumentos)
python generar_plan_subdimension_gd.py "Organización" "Basico"

# Calidad Web (2 argumentos)
python generar_plan_subdimension_cw.py "Accesibilidad web" "Instrumento de evaluación de calidad para sitios web"
```

**Output esperado:**
```
Conectando a PostgreSQL...
✅ Conexión exitosa

Buscando datos para subdimensión: "Autenticación digital"
✅ Datos encontrados

Generando plan con LLM...
Generando indicador de resultado...
Eliminando plan antiguo (si existe)...
Insertando nuevos registros...

✅ Plan generado exitosamente para "Autenticación digital"
Total actividades: 10
Total hitos: 3
```

#### Caso 3: Testear Cambios en SuperPrompt

**Escenario:** Has modificado el SuperPrompt y quieres probar sin procesar todo

```bash
# 1. Modificar SuperPrompt_AgenteMaestro_PTD.md

# 2. Probar con UN plan específico
python generar_plan_subdimension_pa.py "Autenticación digital"

# 3. Verificar resultado en DB
python -c "import psycopg2; from config import DB_CONFIG; conn = psycopg2.connect(**DB_CONFIG); cur = conn.cursor(); cur.execute('SELECT Descripcion FROM ptd_planes WHERE Subdimension = %s LIMIT 5', ('Autenticación digital',)); for row in cur: print(row[0]); conn.close()"

# 4. Si está OK, ejecutar main completo
python main_procedimiento_administrativo.py
```

#### Caso 4: Consultar Planes Generados

**SQL Queries útiles:**

```sql
-- Ver resumen de planes por dimensión
SELECT Dimension, COUNT(*) as total_elementos
FROM ptd_planes
WHERE Autor = 'Agente Maestro'
GROUP BY Dimension;

-- Ver plan completo de una subdimensión
SELECT N_Actividad_Hito, Tipo, Descripcion
FROM ptd_planes
WHERE Subdimension = 'Autenticación digital'
  AND Autor = 'Agente Maestro'
ORDER BY N_Actividad_Hito;

-- Contar actividades vs hitos por subdimensión
SELECT Subdimension, Tipo, COUNT(*) as total
FROM ptd_planes
WHERE Dimension = 'Procedimiento administrativo de función específica'
  AND Autor = 'Agente Maestro'
GROUP BY Subdimension, Tipo
ORDER BY Subdimension, Tipo;

-- Comparar planes Comité vs Agente Maestro
SELECT Autor, COUNT(*) as total_elementos
FROM ptd_planes
WHERE Subdimension = 'Visión Estratégica'
  AND Nivel_de_madurez = 'Basico'
GROUP BY Autor;
```

---

## 📜 Scripts Principales

### Main Scripts (Procesamiento por Lotes)

#### 1. main_procedimiento_administrativo.py

**Propósito:** Generar planes para las 6 subdimensiones de Procedimiento Administrativo

**Características:**
- Lee subdimensiones desde PostgreSQL
- Genera plan + indicador cualitativo
- Parsea plan a registros individuales
- Elimina planes antiguos del Agente Maestro
- Inserta nuevos registros con `Nivel_de_madurez=NULL`
- Commit por subdimensión

**Uso:**
```bash
python main_procedimiento_administrativo.py
```

**Subdimensiones procesadas:**
1. Autenticación digital
2. Interoperabilidad
3. Notificaciones electrónicas
4. Ingreso de solicitudes electrónicas
5. Expedientes electrónicos
6. Comunicaciones oficiales electrónicas

**Tiempo estimado:** 2-4 minutos (6 planes)

**Funciones clave:**
- `leer_subdimensiones_desde_db()`: SELECT DISTINCT
- `generar_plan_ptd()`: LLM generation
- `generar_indicador_resultado()`: Indicador cualitativo
- `parsear_plan_a_registros()`: Parsing a tuples
- `eliminar_plan_antiguo()`: DELETE before INSERT
- `insertar_registro()`: INSERT single record

#### 2. main_gobernanza_datos.py

**Propósito:** Generar ~36 planes para Gobernanza de Datos (12 subdimensiones × 3 niveles)

**Características especiales:**
- Maneja niveles de madurez: Insuficiente → Basico → Medio → Avanzado
- Función `determinar_nivel_siguiente()` para transiciones
- Elimina por 4 parámetros: dimension + subdimension + nivel + autor
- Inserta con `Nivel_de_madurez` poblado
- Prompts enfatizan progresión incremental

**Uso:**
```bash
python main_gobernanza_datos.py
```

**Niveles de madurez:**
- **Insuficiente → Básico:** Establecer bases (definir, crear)
- **Básico → Medio:** Operativizar (implementar, integrar)
- **Medio → Avanzado:** Optimizar (automatizar, consolidar)

**Tiempo estimado:** 12-18 minutos (36 planes)

**Funciones clave:**
- `determinar_nivel_siguiente()`: Mapeo de transiciones
- `leer_subdimensiones_desde_db()`: Incluye Nivel_de_madurez
- Resto similar a PA pero con nivel de madurez

#### 3. main_calidad_web.py

**Propósito:** Generar 40 planes para Calidad Web (22 subdimensiones × instrumentos)

**Características especiales:**
- Procesa 575 preguntas agrupadas en 40 planes únicos
- Genera 1 actividad por pregunta
- Genera 1 hito por indicador (reutilizado)
- **Lógica especial de inserción de hitos:**
  ```python
  for pregunta in actividades_generadas:
      if indicador_cambio and hito_pendiente:
          insertar(hito_pendiente)  # Inserta hito anterior
      insertar(actividad)
      guardar_hito_como_pendiente()
  insertar(ultimo_hito_pendiente)
  ```
- Elimina por 4 parámetros: dimension + subdimension + instrumento + autor

**Uso:**
```bash
python main_calidad_web.py
```

**Agrupaciones:**
- 22 subdimensiones (Accesibilidad web, Usabilidad, etc.)
- 2 instrumentos de evaluación
- 40 combinaciones únicas (subdimension × instrumento)

**Tiempo estimado:** 30-45 minutos (575 preguntas)

**Funciones clave:**
- `leer_preguntas_desde_db()`: Retorna lista de preguntas
- `generar_actividad_para_pregunta()`: Una actividad
- `generar_hito_para_indicador()`: Un hito reutilizable
- Lógica de inserción condicional de hitos

---

### Subscripts (Procesamiento Selectivo)

#### 4. generar_plan_subdimension_pa.py

**Propósito:** Generar plan para UNA subdimensión de Procedimiento Administrativo

**Argumentos:**
```bash
python generar_plan_subdimension_pa.py "<nombre_subdimension>"

# Ejemplo:
python generar_plan_subdimension_pa.py "Autenticación digital"
```

**Validaciones:**
- Verifica que se pase exactamente 1 argumento
- Busca subdimensión en DB con LIMIT 1
- Muestra subdimensiones disponibles si no encuentra

**Subdimensiones disponibles:**
```
- Autenticación digital
- Interoperabilidad
- Notificaciones electrónicas
- Ingreso de solicitudes electrónicas
- Expedientes electrónicos
- Comunicaciones oficiales electrónicas
```

**Tiempo estimado:** 20-40 segundos (1 plan)

#### 5. generar_plan_subdimension_gd.py

**Propósito:** Generar plan para UNA subdimensión + nivel de Gobernanza de Datos

**Argumentos:**
```bash
python generar_plan_subdimension_gd.py "<nombre_subdimension>" "<nivel_madurez>"

# Ejemplo:
python generar_plan_subdimension_gd.py "Organización" "Basico"
```

**Validaciones:**
- Verifica que se pasen exactamente 2 argumentos
- Valida que nivel esté en `['Insuficiente', 'Basico', 'Medio', 'Avanzado']`
- Busca combinación (subdimension, nivel) en DB
- Muestra combinaciones disponibles si no encuentra

**Niveles válidos:**
- `Insuficiente`
- `Basico`
- `Medio`
- `Avanzado`

**Tiempo estimado:** 20-40 segundos (1 plan)

#### 6. generar_plan_subdimension_cw.py

**Propósito:** Generar plan para UNA subdimensión + instrumento de Calidad Web

**Argumentos:**
```bash
python generar_plan_subdimension_cw.py "<nombre_subdimension>" "<instrumento>"

# Ejemplo:
python generar_plan_subdimension_cw.py "Accesibilidad web" "Instrumento de evaluación de calidad para sitios web"
```

**Validaciones:**
- Verifica que se pasen exactamente 2 argumentos
- Busca combinación (subdimension, instrumento) en DB
- Muestra combinaciones disponibles si no encuentra
- Lista nombres comunes de instrumentos en ayuda

**Instrumentos comunes:**
```
- Instrumento de evaluación de calidad para sitios web
- Instrumento de evaluación de servicios digitales
```

**Tiempo estimado:** 30-60 segundos (múltiples preguntas)

---

## 🗄️ Base de Datos

### Esquema de la Tabla `ptd_planes`

```sql
CREATE TABLE ptd_planes (
    id SERIAL PRIMARY KEY,
    
    -- Identificadores
    Dimension VARCHAR(255) NOT NULL,
    Subdimension VARCHAR(255) NOT NULL,
    Instrumento VARCHAR(255),
    Nivel_de_madurez tipo_nivel_madurez,  -- ENUM: Insuficiente/Basico/Medio/Avanzado
    
    -- Contexto
    Brecha TEXT,
    Pregunta TEXT,
    Iniciativa VARCHAR(500),
    Objetivo_Iniciativa TEXT,
    Indicador_Proceso TEXT,
    Indicador_Impacto TEXT,
    
    -- Autor y tipo
    Autor tipo_autor NOT NULL,  -- ENUM: Comite/Agente Maestro
    N_Actividad_Hito INT NOT NULL,
    Tipo tipo_actividad_hito NOT NULL,  -- ENUM: Actividad/Hito
    Descripcion TEXT NOT NULL,
    
    -- Auditoría
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tipos ENUM Personalizados

```sql
-- Niveles de madurez (Gobernanza de Datos)
CREATE TYPE tipo_nivel_madurez AS ENUM (
    'Insuficiente', 
    'Basico', 
    'Medio',
    'Avanzado'
);

-- Autores de planes
CREATE TYPE tipo_autor AS ENUM (
    'Comite',           -- Planes originales del comité
    'Agente Maestro'    -- Planes generados por LLM
);

-- Tipo de elemento
CREATE TYPE tipo_actividad_hito AS ENUM (
    'Actividad',
    'Hito'
);
```

### Índices Optimizados

```sql
CREATE INDEX idx_dimension ON ptd_planes(Dimension);
CREATE INDEX idx_subdimension ON ptd_planes(Subdimension);
CREATE INDEX idx_nivel_madurez ON ptd_planes(Nivel_de_madurez);
CREATE INDEX idx_instrumento ON ptd_planes(Instrumento);
CREATE INDEX idx_autor ON ptd_planes(Autor);
CREATE INDEX idx_tipo ON ptd_planes(Tipo);
```

### Consultas SQL Útiles

Ver documentación completa en `README_SQL.md`

**Ejemplos rápidos:**

```sql
-- Plan completo de una subdimensión
SELECT N_Actividad_Hito, Tipo, Descripcion
FROM ptd_planes
WHERE Subdimension = 'Autenticación digital'
  AND Autor = 'Agente Maestro'
ORDER BY N_Actividad_Hito;

-- Estadísticas por dimensión
SELECT 
    Dimension,
    COUNT(DISTINCT Subdimension) as subdimensiones,
    COUNT(*) as total_elementos,
    SUM(CASE WHEN Tipo = 'Actividad' THEN 1 ELSE 0 END) as actividades,
    SUM(CASE WHEN Tipo = 'Hito' THEN 1 ELSE 0 END) as hitos
FROM ptd_planes
WHERE Autor = 'Agente Maestro'
GROUP BY Dimension;

-- Comparar Comité vs Agente Maestro
SELECT 
    Autor,
    COUNT(*) as total_elementos,
    AVG(LENGTH(Descripcion)) as promedio_palabras
FROM ptd_planes
WHERE Subdimension = 'Visión Estratégica'
  AND Nivel_de_madurez = 'Basico'
GROUP BY Autor;
```

---

## 🤖 SuperPrompt

### Ubicación y Gestión

**Desde la versión 2.1 (Noviembre 2025):**
- 📊 **Base de datos:** Tabla `ptd_prompts` en PostgreSQL
- 🌐 **Interfaz web:** `/prompts/` en el Editor de Planes PTD
- 📝 **Versionado automático:** Cada cambio crea nueva versión con historial
- ⏮️ **Rollback:** Restaurar versiones anteriores con un clic
- 📁 **Fallback:** `SuperPrompt_AgenteMaestro_PTD.md` (1,500+ líneas) si hay error de conexión

**Ventajas del sistema de gestión:**
- ✅ Edición web sin necesidad de archivos `.md`
- ✅ Historial completo de versiones con fechas y notas
- ✅ Cambios se reflejan inmediatamente en scripts (sin reiniciar)
- ✅ Trazabilidad: saber qué versión generó cada plan
- ✅ Restauración rápida ante errores

**Acceso:**
```
http://localhost:5000/prompts/
```

Ver documentación completa: `doc/PROMPTS_README.md`

---

### Componentes Principales del SuperPrompt

1. **Identidad del Agente**
   - Rol: Agente Maestro PTD
   - Combina 3 agentes especializados
   - Objetivo: Automatización PTD

2. **Misión y Alcance**
   - Objetivo principal
   - Flujo de trabajo
   - Estructura de output

3. **Metodología HITOS-FIRST**
   ```
   1. PRIMERO: Crear los HITOS (entregables clave)
   2. SEGUNDO: Generar ACTIVIDADES por cada hito
   ```

4. **Reglas de Generación**
   - Cantidades mínimas por complejidad
   - Actividades 12-25 palabras
   - Hitos 10-20 palabras
   - 100% técnico (sin capacitaciones)

5. **Indicadores Cualitativos**
   - No cuantitativos (sin %, números)
   - Enfoque en impacto/transformación
   - Estructura: [Concepto] + [Estado] + [Contexto]

6. **Reglas por Dimensión**
   - **Procedimiento Administrativo:** 3-4 hitos, 10-16 actividades
   - **Gobernanza de Datos:** Progresión incremental por nivel
   - **Calidad Web:** 1 actividad/pregunta, 1 hito/indicador

7. **Actividades Prohibidas**
   - ❌ Capacitaciones
   - ❌ Evaluaciones post-implementación
   - ❌ Monitoreo continuo
   - ❌ Optimizaciones post-cierre
   - Regla de Oro: "Si es DESPUÉS de cerrar brecha, NO incluir"

8. **Reporteo en Terminal**
   - Mostrar hitos generados
   - Mostrar actividades por hito
   - Mensaje de éxito final

### Cómo se Desarrolló el SuperPrompt

Ver documentación completa en `DESARROLLO_SUPERPROMPT.md`

---

## 🔧 Adaptación a Otros PMG

### Proceso de Adaptación General

Este sistema está diseñado para ser **adaptable a otros PMG** con diferentes dimensiones, variables y brechas. Dado que cada PMG puede tener una estructura totalmente distinta, el proceso de adaptación debe ser evaluado caso a caso.

> ⚠️ **Nota Importante:** Cada PMG tiene características únicas (dimensiones, subdimensiones, niveles de madurez, indicadores, etc.). No existe un ejemplo universal aplicable a todos los casos. El proceso debe ser analizado individualmente según el PMG objetivo.

### Checklist de Adaptación

#### 1. Análisis del Nuevo PMG
- [ ] Identificar dimensiones del PMG
- [ ] Identificar subdimensiones por cada dimensión
- [ ] Determinar si existen niveles de madurez
- [ ] Analizar estructura del diagnóstico
- [ ] Identificar indicadores y métricas
- [ ] Comprender flujo de trabajo específico
- [ ] Analizar formato de output esperado

#### 2. Base de Datos
- [ ] Analizar diferencias en estructura de datos
- [ ] Crear/modificar tipos ENUM en PostgreSQL según necesidad
- [ ] Adaptar esquema de tabla `ptd_planes`
- [ ] Agregar columnas específicas si es necesario
- [ ] Actualizar índices para optimizar consultas
- [ ] Crear scripts SQL para el nuevo PMG
- [ ] Probar integridad referencial

#### 3. SuperPrompt
- [ ] Crear nuevo SuperPrompt específico para el PMG
- [ ] Actualizar identidad del agente
- [ ] Definir dimensiones y subdimensiones
- [ ] Establecer reglas de generación específicas
- [ ] Agregar ejemplos contextualizados al PMG
- [ ] Definir metodología de generación (HITOS-FIRST u otra)
- [ ] Especificar cantidades y restricciones
- [ ] Documentar actividades prohibidas/permitidas

#### 4. Scripts de Generación
- [ ] Desarrollar main scripts por dimensión
- [ ] Desarrollar subscripts para generación selectiva
- [ ] Adaptar funciones de lectura de datos desde DB
- [ ] Actualizar lógica de parseo de respuestas LLM
- [ ] Implementar validaciones específicas del PMG
- [ ] Configurar parámetros del LLM (temperatura, modelo)
- [ ] Actualizar queries SQL según nuevo esquema

#### 5. Configuración
- [ ] Actualizar `config.py` si es necesario
- [ ] Agregar variables de entorno específicas al `.env`
- [ ] Configurar credenciales de APIs
- [ ] Ajustar timeouts y límites de tokens
- [ ] Configurar logging específico

#### 6. Testing y Validación
- [ ] Crear scripts de prueba unitarios
- [ ] Probar generación con subscripts (casos individuales)
- [ ] Validar formato de output
- [ ] Verificar calidad del contenido generado
- [ ] Probar procesamiento por lotes (main scripts)
- [ ] Validar inserción correcta en base de datos
- [ ] Realizar pruebas de integración completas

#### 7. Documentación
- [ ] Crear README específico del nuevo PMG
- [ ] Documentar decisiones de diseño
- [ ] Incluir ejemplos de uso
- [ ] Documentar estructura de datos
- [ ] Crear guía de troubleshooting específica
- [ ] Documentar limitaciones conocidas
- [ ] Validar documentación con expertos del dominio

#### 8. Validación con Expertos
- [ ] Revisar generación con expertos del PMG
- [ ] Ajustar SuperPrompt según feedback
- [ ] Iterar hasta alcanzar calidad aceptable
- [ ] Documentar ajustes realizados
- [ ] Obtener aprobación final

### Recursos de Referencia

Para entender cómo fue desarrollado este sistema:
- **`HISTORIAL_DESARROLLO.md`**: Cronología completa del desarrollo
- **`DESARROLLO_SUPERPROMPT.md`**: Evolución del SuperPrompt (11 versiones)
- **`CHANGELOG.md`**: Log detallado de todos los cambios realizados
- **Scripts existentes**: `main_*.py` y `generar_*.py` como templates

### Recomendaciones

1. **Comenzar pequeño:** Probar con una dimensión antes de escalar
2. **Iterar frecuentemente:** El SuperPrompt requiere múltiples ajustes
3. **Validar constantemente:** Revisar calidad después de cada cambio
4. **Documentar todo:** Cada decisión debe quedar registrada
5. **Mantener arquitectura dual:** Main scripts + subscripts para flexibilidad

---

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a PostgreSQL

**Síntomas:**
```
psycopg2.OperationalError: could not connect to server
```

**Soluciones:**
```bash
# Verificar que PostgreSQL esté corriendo
psql -h localhost -p 5432 -U postgres -d ptd_db -c "SELECT 1"

# Verificar variables de entorno
cat .env | grep POSTGRES

# Probar conexión con Python
python -c "import psycopg2; from config import DB_CONFIG; conn = psycopg2.connect(**DB_CONFIG); print('✅ Conexión exitosa'); conn.close()"

# Revisar host y puerto en .env
# Asegurar que POSTGRES_HOST y POSTGRES_PORT sean correctos
```

#### 2. Error de OpenAI API Key

**Síntomas:**
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Soluciones:**
```bash
# Verificar que .env tenga la key correcta
cat .env | grep OPENAI_API_KEY

# Probar key manualmente
python -c "from openai import OpenAI; client = OpenAI(api_key='tu-key'); print(client.models.list())"

# Regenerar key en https://platform.openai.com/api-keys
```

#### 3. Script No Genera Planes

**Síntomas:**
- Script ejecuta pero no inserta nada en DB
- Mensaje "0 planes generados"

**Soluciones:**
```bash
# Verificar que haya datos en la tabla
python -c "import psycopg2; from config import DB_CONFIG; conn = psycopg2.connect(**DB_CONFIG); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM ptd_planes'); print(f'Total registros: {cur.fetchone()[0]}'); conn.close()"

# Verificar filtros en query del script
# Revisar que Dimension, Subdimension coincidan con DB

# Ejecutar en modo debug
python -c "import sys; sys.argv = ['', 'Autenticación digital']; exec(open('generar_plan_subdimension_pa.py').read())"
```

#### 4. Planes Muy Cortos o Genéricos

**Causa:** SuperPrompt no está siendo seguido

**Soluciones:**
1. Verificar que el SuperPrompt se está cargando desde la base de datos:
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
           if resultado:
               print(f"✅ SuperPrompt cargado desde BD: {len(resultado[0])} caracteres")
               return resultado[0]
           else:
               print("⚠️ No se encontró SuperPrompt en BD, usando archivo .md")
               with open('SuperPrompt_AgenteMaestro_PTD.md', 'r', encoding='utf-8') as f:
                   content = f.read()
               print(f"SuperPrompt cargado desde archivo: {len(content)} caracteres")
               return content
               
       except Exception as e:
           print(f"❌ Error cargando desde BD: {e}")
           print("⚠️ Usando archivo .md como fallback")
           with open('SuperPrompt_AgenteMaestro_PTD.md', 'r', encoding='utf-8') as f:
               content = f.read()
           return content
   ```
   
   **Nota:** Desde la versión 2.1, todos los scripts cargan el SuperPrompt desde la tabla `ptd_prompts` de la base de datos, usando la versión más reciente (último registro). Esto permite gestionar el prompt desde la interfaz web (`/prompts/`) sin editar archivos `.md`. El archivo físico solo se usa como fallback si hay error de conexión.

2. Aumentar temperatura si planes son muy repetitivos:
   ```python
   llm = ChatOpenAI(
       model="gpt-4o",
       temperature=0.5,  # Aumentar de 0.3 a 0.5
       api_key=os.getenv("OPENAI_API_KEY")
   )
   ```

3. Agregar ejemplos más específicos en el prompt

#### 5. Rate Limit de OpenAI

**Síntomas:**
```
openai.error.RateLimitError: Rate limit reached
```

**Soluciones:**
```python
import time

def generar_con_retry(prompt, max_retries=3):
    for i in range(max_retries):
        try:
            response = llm.invoke(prompt)
            return response.content
        except openai.error.RateLimitError:
            wait_time = (i + 1) * 10  # 10, 20, 30 segundos
            print(f"⏳ Rate limit alcanzado. Esperando {wait_time}s...")
            time.sleep(wait_time)
    raise Exception("Rate limit después de 3 intentos")
```

### Logs y Debugging

**Activar logging detallado:**

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ptd_generation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# En tu código:
logger.debug("Conectando a PostgreSQL...")
logger.info(f"Procesando subdimensión: {subdimension}")
logger.error(f"Error al generar plan: {str(e)}")
```

---

## 🤝 Contribución

### Cómo Contribuir

1. **Fork del repositorio**
2. **Crear branch de feature:**
   ```bash
   git checkout -b feature/nueva-dimension
   ```

3. **Hacer cambios y commit:**
   ```bash
   git add .
   git commit -m "feat: agregar soporte para PMG Gestión de Personas"
   ```

4. **Push y crear Pull Request:**
   ```bash
   git push origin feature/nueva-dimension
   ```

### Convenciones de Código

- **Estilo:** PEP 8 para Python
- **Docstrings:** Google style
- **Commits:** Conventional Commits
- **Branches:** `feature/`, `fix/`, `docs/`

### Testing

```bash
# Ejecutar tests (cuando existan)
pytest tests/

# Ejecutar linter
flake8 *.py

# Ejecutar type checker
mypy *.py
```

---

## 📄 Licencia

Este proyecto está licenciado bajo MIT License. Ver `LICENSE` para más detalles.

---

## 📞 Contacto y Soporte

- **Repositorio:** [github.com/VTI-Equipo-IA/PMG](https://github.com/VTI-Equipo-IA/PMG)
- **Issues:** [github.com/VTI-Equipo-IA/PMG/issues](https://github.com/VTI-Equipo-IA/PMG/issues)
- **Documentación adicional:**
  - `HISTORIAL_DESARROLLO.md`: Historial completo del proyecto
  - `DESARROLLO_SUPERPROMPT.md`: Cómo se creó el SuperPrompt
  - `README_SQL.md`: Guía de base de datos

---

## 🙏 Agradecimientos

- Equipo PMG Transformación Digital
- Gobierno Digital de Chile
- Comunidad LangChain
- OpenAI
