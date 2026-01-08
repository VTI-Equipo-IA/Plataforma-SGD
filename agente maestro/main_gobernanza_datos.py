"""
Script Unificado: Generación e Inserción de Planes PTD - Gobernanza de Datos
Procesa subdimensiones desde PostgreSQL → Genera planes con LLM → Actualiza PostgreSQL
Fecha: 2025-11-05

FLUJO:
1. Lee subdimensiones desde PostgreSQL (por Dimension, Subdimension, Instrumento, Nivel de Madurez)
2. Genera plan PTD para cada subdimensión usando LLM
3. Genera indicador de resultado
4. Parsea el plan (separa actividades/hitos)
5. Elimina plan antiguo (Agente Maestro) si existe
6. Inserta nuevo plan directamente en PostgreSQL
7. Repite para todas las subdimensiones y niveles de madurez
"""

import os
import sys
import psycopg2
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import uuid

# Agregar el directorio padre al path para importar services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.tracked_llm import create_tracked_llm
from services.token_tracker import extract_usage_from_response

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Cargar variables de entorno
load_dotenv()

# Configuración PostgreSQL
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'ptd_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

# Configuración OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY no encontrada en .env")

# Generar ID único para esta ejecución (agrupa todas las llamadas de este proceso)
GRUPO_PROCESOS = f"maestro_gd_{uuid.uuid4().hex[:12]}"
print(f"🔍 ID de grupo de procesos: {GRUPO_PROCESOS}")

# LLM con tracking automático de consumo
llm = create_tracked_llm(
    model="gpt-4o",
    temperature=0.3,
    app_name="PMG",
    grupo_procesos=GRUPO_PROCESOS,
    track_enabled=True
)

# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def conectar_db():
    """Establece conexión con PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        raise

def eliminar_plan_antiguo(conn, dimension, subdimension, nivel_madurez, autor):
    """
    Elimina los registros antiguos de un plan específico de Gobernanza
    
    Args:
        conn: Conexión a PostgreSQL
        dimension: Dimensión del plan
        subdimension: Subdimensión del plan
        nivel_madurez: Nivel de madurez del plan
        autor: Autor del plan ('Agente Maestro' o 'Comite')
        
    Returns:
        Número de registros eliminados
    """
    cursor = conn.cursor()
    
    sql = """
    DELETE FROM ptd_planes
    WHERE Dimension = %s
      AND Subdimension = %s
      AND Nivel_de_madurez = %s
      AND Autor = %s
    """
    
    try:
        cursor.execute(sql, (dimension, subdimension, nivel_madurez, autor))
        registros_eliminados = cursor.rowcount
        cursor.close()
        return registros_eliminados
    except Exception as e:
        print(f"  ❌ Error eliminando plan antiguo: {e}")
        cursor.close()
        raise

def insertar_registro(conn, datos_fila, n_secuencial, tipo, descripcion):
    """
    Inserta un registro (actividad o hito) en la base de datos
    
    Args:
        conn: Conexión a PostgreSQL
        datos_fila: Diccionario con datos comunes
        n_secuencial: Número secuencial de la actividad/hito
        tipo: 'Actividad' o 'Hito'
        descripcion: Texto de la actividad o hito
    """
    cursor = conn.cursor()
    
    sql = """
    INSERT INTO ptd_planes (
        Dimension,
        Subdimension,
        Instrumento,
        Indicador,
        Brecha,
        Nivel_de_madurez,
        N_Pregunta,
        Pregunta,
        Iniciativa,
        Objetivo_Iniciativa,
        Autor,
        Indicador_Proceso,
        Indicador_Resultado,
        N_Actividad_Hito,
        Tipo,
        Descripcion
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    
    valores = (
        datos_fila['dimension'],
        datos_fila['subdimension'],
        datos_fila['instrumento'],
        datos_fila['indicador'],
        datos_fila['brecha'],
        datos_fila['nivel_madurez'],  # Gobernanza tiene nivel de madurez
        None,  # N_Pregunta (NULL para Gobernanza)
        None,  # Pregunta (NULL para Gobernanza)
        datos_fila['iniciativa'],
        datos_fila['objetivo_iniciativa'],
        datos_fila['autor'],
        datos_fila['indicador_proceso'],
        datos_fila['indicador_resultado'],
        n_secuencial,
        tipo,
        descripcion
    )
    
    try:
        cursor.execute(sql, valores)
        cursor.close()
        return True
    except Exception as e:
        print(f"  ❌ Error insertando registro {n_secuencial} ({tipo}): {e}")
        cursor.close()
        raise

# ============================================================================
# FUNCIONES DE LECTURA DE DATOS DE ENTRADA
# ============================================================================

def leer_subdimensiones_desde_db(conn):
    """
    Lee las subdimensiones directamente desde PostgreSQL
    Busca por Dimension, Subdimension, Instrumento y Nivel_de_madurez para obtener planes únicos
    
    Args:
        conn: Conexión a PostgreSQL
        
    Returns:
        Lista de diccionarios con los datos necesarios
    """
    print("\n" + "="*80)
    print("📂 LEYENDO SUBDIMENSIONES DESDE POSTGRESQL")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
    # Query para obtener subdimensiones únicas con sus datos
    # Agrupamos por Dimension, Subdimension, Instrumento, Nivel_de_madurez
    sql = """
    SELECT DISTINCT
        Dimension,
        Subdimension,
        Instrumento,
        Indicador,
        Brecha,
        Nivel_de_madurez,
        Iniciativa,
        Objetivo_Iniciativa,
        Indicador_Proceso
    FROM ptd_planes
    WHERE Dimension = 'Gobernanza de datos'
      AND Nivel_de_madurez IS NOT NULL
    ORDER BY Subdimension, Nivel_de_madurez
    """
    
    try:
        cursor.execute(sql)
        filas = cursor.fetchall()
        
        subdimensiones = []
        
        for fila in filas:
            subdimension_data = {
                'dimension': fila[0],
                'subdimension': fila[1],
                'instrumento': fila[2],
                'indicador': fila[3],
                'brecha': fila[4],
                'nivel_madurez': fila[5],
                'iniciativa': fila[6],
                'objetivo_iniciativa': fila[7],
                'indicador_proceso': fila[8],
                # Datos adicionales para el LLM
                'n_pregunta': None,  # No se usa en Gobernanza
                'preguntas_condensadas': 'Preguntas del Marco MGDE respondidas negativamente',
                'nombre_iniciativa': fila[6]  # Usar mismo valor que iniciativa
            }
            
            subdimensiones.append(subdimension_data)
            print(f"  ✅ Leída: {subdimension_data['subdimension']} - Nivel: {subdimension_data['nivel_madurez']}")
        
        cursor.close()
        
        print(f"\n📊 Total planes únicos leídos: {len(subdimensiones)}\n")
        
        return subdimensiones
        
    except Exception as e:
        print(f"❌ Error leyendo subdimensiones: {e}")
        cursor.close()
        raise

# ============================================================================
# FUNCIONES DE GENERACIÓN DE PLANES CON LLM
# ============================================================================

def cargar_superprompt():
    """Carga el SuperPrompt desde la base de datos (versión más reciente)"""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Obtener el prompt con el ID más alto (más reciente)
        cursor.execute("""
            SELECT prompt 
            FROM ptd_prompts 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if resultado:
            return resultado[0]
        else:
            raise ValueError("No se encontró ningún prompt en la base de datos")
            
    except Exception as e:
        print(f"❌ Error cargando SuperPrompt desde base de datos: {e}")
        print("⚠️  Intentando cargar desde archivo .md como fallback...")
        superprompt_path = r"SuperPrompt_AgenteMaestro_PTD.md"
        with open(superprompt_path, 'r', encoding='utf-8') as f:
            return f.read()

def determinar_nivel_siguiente(nivel_actual):
    """Determina el nivel de madurez siguiente"""
    niveles = {
        'Insuficiente': 'Basico',
        'Basico': 'Medio',
        'Medio': 'Avanzado',
        'Avanzado': 'Avanzado (consolidado)'
    }
    return niveles.get(nivel_actual, 'Desconocido')

def generar_plan_ptd(datos_subdimension, superprompt):
    """
    Genera un plan PTD usando el LLM para Gobernanza de Datos
    
    Args:
        datos_subdimension: Dict con datos de la subdimensión
        superprompt: Texto del SuperPrompt
        
    Returns:
        String con el plan en formato:
        Actividad: ...
        Actividad: ...
        Hito: ...
    """
    nivel_siguiente = determinar_nivel_siguiente(datos_subdimension['nivel_madurez'])
    
    print(f"\n{'='*80}")
    print(f"🤖 GENERANDO PLAN: {datos_subdimension['subdimension']}")
    print(f"   Nivel: {datos_subdimension['nivel_madurez']} → {nivel_siguiente}")
    print(f"{'='*80}\n")
    
    template = """
{superprompt}

---

## TAREA ESPECÍFICA: Generar Plan PTD para Gobernanza de Datos

**Datos de la Subdimensión**:
- Dimensión: {dimension}
- Subdimensión: {subdimension}
- Instrumento: {instrumento}
- Indicador: {indicador}
- Brecha: {brecha}
- **Nivel de Madurez ACTUAL**: {nivel_madurez}
- **Nivel de Madurez OBJETIVO**: {nivel_siguiente}
- Preguntas (todas con respuesta NEGATIVA): {preguntas_condensadas}
- Iniciativa: {iniciativa}
- Objetivo de Iniciativa: {objetivo_iniciativa}
- Indicador Proceso: {indicador_proceso}
- Nombre Iniciativa: {nombre_iniciativa}

**INSTRUCCIONES CRÍTICAS**:
1. Genera un plan completo siguiendo la metodología HITOS-FIRST
2. El plan debe permitir pasar del nivel **{nivel_madurez}** al nivel **{nivel_siguiente}**
3. **NO se puede "saltar niveles"** - enfócate en el salto específico del nivel actual al siguiente
4. **🎯 CANTIDAD OBLIGATORIA**:
   - Genera SOLO **3 HITOS MÁXIMO**
   - Cada hito debe tener **3-4 ACTIVIDADES**
   - Total esperado: **9-12 actividades MÁXIMO**
5. **📈 PROGRESIÓN INCREMENTAL OBLIGATORIA (CRÍTICO - NO REPETIR ACTIVIDADES)**:
   - Si estás generando plan para nivel **{nivel_madurez} → {nivel_siguiente}**, asume que YA SE COMPLETARON las actividades de niveles anteriores
   - **PROHIBIDO repetir actividades de niveles previos**
   - **Cada nivel debe CONSTRUIR sobre el anterior**, no repetirlo
   - Verbos por nivel de madurez:
     * Insuficiente→Basico: Definir, Crear, Establecer, Identificar, Configurar (inicial)
     * Basico→Medio: Implementar, Integrar, Desplegar, Aplicar, Expandir (lo ya definido)
     * Medio→Avanzado: Automatizar, Optimizar, Consolidar, Escalar, Certificar (lo ya implementado)
6. **🔧 ENFOQUE 100% TÉCNICO - SOLO IMPLEMENTACIÓN**:
   - **LA ÚLTIMA ACTIVIDAD/HITO DEBE ALCANZAR EL NIVEL SIGUIENTE - NO agregar trabajo adicional posterior**
   - **PROHIBIDO incluir**: capacitaciones, evaluaciones, auditorías periódicas, monitoreo post-implementación
   - **PERMITIDO**: configuración, desarrollo, implementación, integración, pruebas, despliegue, certificación

**🚨 REGLAS DE ESPECIFICIDAD OBLIGATORIAS**:
1. **CADA actividad debe tener entre 12-25 palabras** (NO menos de 12)
2. **CADA hito debe tener entre 10-20 palabras** (NO menos de 10)
3. **OBLIGATORIO especificar**:
   - QUÉ documento/herramienta exactamente (Política Institucional de Datos, Comité de Datos, etc.)
   - DÓNDE se aplicará (áreas, sistemas, procesos específicos)
   - CÓMO se implementará técnicamente (conforme al Marco MGDE, usando roles específicos, etc.)

**SOLO PARA SUBDIMENSIÓN "{subdimension}"**:
- ❌ NO mencionar otras subdimensiones
- ✅ SOLO actividades relacionadas con "{subdimension}"

**FORMATO DE SALIDA REQUERIDO** (ACTIVIDADES PRIMERO, HITO DESPUÉS):
```
Actividad: [Actividad 1.1]
Actividad: [Actividad 1.2]
Actividad: [Actividad 1.3]
Hito: [Descripción del hito 1]
Actividad: [Actividad 2.1]
Actividad: [Actividad 2.2]
Actividad: [Actividad 2.3]
Hito: [Descripción del hito 2]
...
Actividad: [ÚLTIMA - Certificar nivel {nivel_siguiente}]
Hito: [Hito final que alcanza nivel {nivel_siguiente}]
```

**CRÍTICO**: 
- Las ACTIVIDADES van PRIMERO, el HITO va DESPUÉS de sus actividades
- Devuelve SOLO el plan en formato texto plano
- NO incluyas marcadores de código (```) ni explicaciones adicionales
- Cada línea debe empezar con "Hito: " o "Actividad: "
- MÁXIMO 3 hitos con 9-12 actividades total
- Enfócate en pasar de {nivel_madurez} a {nivel_siguiente}
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    print("🔄 Generando plan con LLM...")
    
    response = chain.invoke({
        "superprompt": superprompt,
        "dimension": datos_subdimension['dimension'],
        "subdimension": datos_subdimension['subdimension'],
        "instrumento": datos_subdimension['instrumento'],
        "indicador": datos_subdimension['indicador'],
        "brecha": datos_subdimension['brecha'],
        "nivel_madurez": datos_subdimension['nivel_madurez'],
        "nivel_siguiente": nivel_siguiente,
        "preguntas_condensadas": datos_subdimension['preguntas_condensadas'],
        "iniciativa": datos_subdimension['iniciativa'],
        "objetivo_iniciativa": datos_subdimension['objetivo_iniciativa'],
        "indicador_proceso": datos_subdimension['indicador_proceso'],
        "nombre_iniciativa": datos_subdimension['nombre_iniciativa']
    })
    
    # Limpiar plan (eliminar backticks si existen)
    plan_generado = response.content.strip()
    if plan_generado.startswith('```'):
        lineas = plan_generado.split('\n')
        lineas = [l for l in lineas if not l.strip().startswith('```')]
        plan_generado = '\n'.join(lineas).strip()
    
    # Análisis del plan
    lineas = plan_generado.split('\n')
    hitos = [l for l in lineas if l.strip().startswith('Hito:')]
    actividades = [l for l in lineas if l.strip().startswith('Actividad:')]
    
    print(f"✅ Plan generado:")
    print(f"   → {len(hitos)} Hitos")
    print(f"   → {len(actividades)} Actividades")
    print(f"   → Total: {len(hitos) + len(actividades)} elementos\n")
    
    return plan_generado

def generar_indicador_resultado(datos_subdimension, plan_generado):
    """
    Genera un indicador cualitativo de resultado para Gobernanza de Datos
    
    Args:
        datos_subdimension: Dict con datos de la subdimensión
        plan_generado: String con el plan PTD generado
        
    Returns:
        String con el indicador de resultado
    """
    nivel_siguiente = determinar_nivel_siguiente(datos_subdimension['nivel_madurez'])
    
    print("🔄 Generando indicador de resultado...")
    
    template = """
Eres un experto en diseño de indicadores de resultado para planes de Gobernanza de Datos del gobierno chileno (Marco MGDE).

**CONTEXTO**:
- Subdimensión MGDE: {subdimension}
- Nivel de Madurez ACTUAL: {nivel_actual}
- Nivel de Madurez OBJETIVO: {nivel_objetivo}
- Iniciativa: {iniciativa}
- Plan a medir (actividades e hitos):
{plan}

**INDICADOR DE RESULTADO - ENFOQUE CUALITATIVO**:

El indicador de resultado debe ser CUALITATIVO y describir el IMPACTO o CAMBIO DE MADUREZ logrado.

**DIFERENCIA FUNDAMENTAL**:
- ❌ **Indicador Proceso** (cuantitativo): "% de políticas de datos implementadas"
- ✅ **Indicador Resultado** (cualitativo): "Política Institucional de Datos formalizada y operativa como marco normativo de gobierno de datos en nivel {nivel_objetivo}"

**CARACTERÍSTICAS DEL INDICADOR DE RESULTADO**:
1. **Cualitativo**: Describe el estado de madurez alcanzado, NO una medición
2. **De Impacto**: Refleja el cambio de capacidad institucional en gestión de datos
3. **Específico al Nivel**: Debe reflejar claramente el nivel {nivel_objetivo} de madurez MGDE
4. **Integral**: Abarca el propósito completo de la subdimensión en ese nivel
5. **Institucional**: Refleja la capacidad organizacional de gestión de datos

**ESTRUCTURA OBLIGATORIA**:
[Capacidad/Proceso MGDE] + [Estado de madurez] + [Contexto del nivel {nivel_objetivo}]

**VERBOS/ESTADOS POR NIVEL**:
- **Nivel Basico**: "establecido", "formalizado", "documentado", "definido"
- **Nivel Medio**: "operativo", "implementado", "en funcionamiento", "aplicado"
- **Nivel Avanzado**: "optimizado", "consolidado", "institucionalizado", "maduro"

**REGLAS ESTRICTAS**:
- Responde SOLO con el texto del indicador (una sola línea)
- NO incluyas explicaciones adicionales
- NO uses comillas ni puntos al final
- Máximo 150 caracteres
- **PROHIBIDO** usar porcentajes (%), números, cantidades
- **OBLIGATORIO** usar verbos de estado apropiados al nivel de madurez
- **OBLIGATORIO** mencionar el contexto MGDE o subdimensión específica

**GENERA EL INDICADOR CUALITATIVO AHORA**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "subdimension": datos_subdimension['subdimension'],
        "nivel_actual": datos_subdimension['nivel_madurez'],
        "nivel_objetivo": nivel_siguiente,
        "iniciativa": datos_subdimension['iniciativa'],
        "plan": plan_generado
    })
    
    # Limpiar indicador
    indicador = response.content.strip()
    indicador = indicador.strip('"').strip("'")
    if indicador.endswith('.'):
        indicador = indicador[:-1]
    
    print(f"✅ Indicador de resultado: {indicador}\n")
    
    return indicador

# ============================================================================
# FUNCIONES DE PARSEO DE PLANES
# ============================================================================

def parsear_plan_a_registros(plan_texto):
    """
    Parsea el plan generado y extrae actividades e hitos
    
    Formato esperado:
    Actividad: Descripción de la actividad
    Hito: Descripción del hito
    
    Returns:
        Lista de tuplas (numero, tipo, descripcion)
    """
    if not plan_texto or str(plan_texto).strip() == '':
        return []
    
    elementos = []
    lineas = str(plan_texto).strip().split('\n')
    numero = 1
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        
        # Detectar si es Actividad o Hito
        if linea.startswith('Actividad:'):
            tipo = 'Actividad'
            descripcion = linea.replace('Actividad:', '').strip()
        elif linea.startswith('Hito:'):
            tipo = 'Hito'
            descripcion = linea.replace('Hito:', '').strip()
        else:
            # Si no tiene prefijo, asumir que es continuación de la descripción anterior
            if elementos:
                elementos[-1] = (elementos[-1][0], elementos[-1][1], elementos[-1][2] + ' ' + linea)
            continue
        
        elementos.append((numero, tipo, descripcion))
        numero += 1
    
    return elementos

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Función principal que ejecuta el flujo completo:
    1. Leer subdimensiones desde PostgreSQL (búsqueda por Dimension, Subdimension, Instrumento, Nivel_de_madurez)
    2. Generar plan PTD para cada subdimensión con LLM
    3. Generar indicador de resultado
    4. Parsear plan (separar actividades/hitos)
    5. Eliminar plan antiguo (Agente Maestro) si existe
    6. Insertar nuevo plan en PostgreSQL
    7. Repetir para todas las subdimensiones y niveles
    """
    print("\n" + "="*80)
    print("🚀 INICIO: GENERACIÓN E INSERCIÓN DE PLANES PTD")
    print("   Gobernanza de Datos (MGDE) → PostgreSQL")
    print("="*80 + "\n")
    
    # Paso 0: Cargar SuperPrompt
    print("📖 Cargando SuperPrompt...")
    superprompt = cargar_superprompt()
    print("✅ SuperPrompt cargado\n")
    
    # Conectar a base de datos
    print("🔌 Conectando a PostgreSQL...")
    conn = conectar_db()
    print(f"✅ Conectado a: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}\n")
    
    conn.autocommit = False  # Usar transacciones
    
    # Paso 1: Leer subdimensiones desde PostgreSQL
    subdimensiones = leer_subdimensiones_desde_db(conn)
    
    # Estadísticas
    total_subdimensiones = len(subdimensiones)
    subdimensiones_procesadas = 0
    total_registros_insertados = 0
    
    # Procesar cada subdimensión
    for idx, datos_subdimension in enumerate(subdimensiones, 1):
        print("\n" + "="*80)
        print(f"📋 PROCESANDO PLAN {idx}/{total_subdimensiones}")
        print(f"   {datos_subdimension['subdimension']} - Nivel: {datos_subdimension['nivel_madurez']}")
        print("="*80)
        
        try:
            # Paso 2: Generar plan PTD
            plan_generado = generar_plan_ptd(datos_subdimension, superprompt)
            
            # Paso 3: Generar indicador de resultado
            indicador_resultado = generar_indicador_resultado(datos_subdimension, plan_generado)
            
            # Paso 4: Parsear plan
            print("🔄 Parseando plan...")
            elementos = parsear_plan_a_registros(plan_generado)
            
            if not elementos:
                print(f"⚠️  Plan vacío después de parsear. Omitiendo subdimensión.")
                continue
            
            print(f"✅ Plan parseado: {len(elementos)} elementos")
            actividades_count = sum(1 for e in elementos if e[1] == 'Actividad')
            hitos_count = sum(1 for e in elementos if e[1] == 'Hito')
            print(f"   → {actividades_count} Actividades")
            print(f"   → {hitos_count} Hitos\n")
            
            # Paso 5: Eliminar plan antiguo si existe
            print("🗑️  Verificando y eliminando plan antiguo...")
            registros_eliminados = eliminar_plan_antiguo(
                conn,
                datos_subdimension['dimension'],
                datos_subdimension['subdimension'],
                datos_subdimension['nivel_madurez'],
                'Agente Maestro'
            )
            
            if registros_eliminados > 0:
                print(f"✅ Plan antiguo eliminado: {registros_eliminados} registros")
            else:
                print(f"ℹ️  No se encontró plan antiguo para eliminar")
            
            # Paso 6: Insertar nuevo plan en PostgreSQL
            print("💾 Insertando nuevo plan en base de datos...")
            
            # Preparar datos comunes
            datos_fila = {
                'dimension': datos_subdimension['dimension'],
                'subdimension': datos_subdimension['subdimension'],
                'instrumento': datos_subdimension['instrumento'],
                'indicador': datos_subdimension['indicador'],
                'brecha': datos_subdimension['brecha'],
                'nivel_madurez': datos_subdimension['nivel_madurez'],
                'iniciativa': datos_subdimension['iniciativa'],
                'objetivo_iniciativa': datos_subdimension['objetivo_iniciativa'],
                'autor': 'Agente Maestro',  # Script genera planes como Agente Maestro
                'indicador_proceso': datos_subdimension['indicador_proceso'],
                'indicador_resultado': indicador_resultado
            }
            
            # Insertar cada elemento
            for numero, tipo, descripcion in elementos:
                insertar_registro(conn, datos_fila, numero, tipo, descripcion)
            
            # Commit de la subdimensión
            conn.commit()
            
            subdimensiones_procesadas += 1
            total_registros_insertados += len(elementos)
            
            print(f"✅ Subdimensión completada:")
            print(f"   → Plan antiguo: {registros_eliminados} registros eliminados")
            print(f"   → Plan nuevo: {len(elementos)} registros insertados\n")
            
        except Exception as e:
            print(f"\n❌ Error procesando plan '{datos_subdimension['subdimension']}' (Nivel {datos_subdimension['nivel_madurez']}): {e}")
            conn.rollback()
            print("🔄 Continuando con siguiente plan...\n")
            continue
    
    # Cerrar conexión
    conn.close()
    
    # Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"✅ Planes procesados: {subdimensiones_procesadas}/{total_subdimensiones}")
    print(f"✅ Total registros insertados: {total_registros_insertados}")
    print(f"📊 Promedio registros/plan: {total_registros_insertados/subdimensiones_procesadas:.1f}" if subdimensiones_procesadas > 0 else "")
    print("="*80)
    
    # Verificación final en base de datos
    print("\n🔍 Verificando datos en PostgreSQL...")
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Contar registros por subdimensión y nivel
    cursor.execute("""
        SELECT Subdimension, Nivel_de_madurez, COUNT(*) as total
        FROM ptd_planes
        WHERE Dimension = 'Gobernanza de datos'
          AND Autor = 'Agente Maestro'
        GROUP BY Subdimension, Nivel_de_madurez
        ORDER BY Subdimension, Nivel_de_madurez
    """)
    
    print("\n📊 Registros por subdimensión y nivel:")
    for subdim, nivel, total in cursor.fetchall():
        print(f"   • {subdim} ({nivel}): {total} registros")
    
    # Contar por tipo
    cursor.execute("""
        SELECT Tipo, COUNT(*) as total
        FROM ptd_planes
        WHERE Dimension = 'Gobernanza de datos'
          AND Autor = 'Agente Maestro'
        GROUP BY Tipo
        ORDER BY total DESC
    """)
    
    print("\n📊 Registros por tipo:")
    for tipo, total in cursor.fetchall():
        print(f"   • {tipo}: {total} registros")
    
    # Contar por nivel de madurez
    cursor.execute("""
        SELECT Nivel_de_madurez, COUNT(*) as total
        FROM ptd_planes
        WHERE Dimension = 'Gobernanza de datos'
          AND Autor = 'Agente Maestro'
        GROUP BY Nivel_de_madurez
        ORDER BY 
            CASE Nivel_de_madurez
                WHEN 'Insuficiente' THEN 1
                WHEN 'Basico' THEN 2
                WHEN 'Medio' THEN 3
                ELSE 4
            END
    """)
    
    print("\n📊 Registros por nivel de madurez:")
    for nivel, total in cursor.fetchall():
        print(f"   • {nivel}: {total} registros")
    
    cursor.close()
    conn.close()
    
    print("\n✅ PROCESO COMPLETADO EXITOSAMENTE!\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        raise
