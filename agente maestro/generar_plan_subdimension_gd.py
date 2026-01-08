"""
Subscript: Generación de Plan PTD para UNA Subdimensión de Gobernanza de Datos
Procesa una subdimensión específica (con nivel de madurez) desde PostgreSQL → Genera plan con LLM → Actualiza PostgreSQL
Fecha: 2025-11-05

USO:
    python generar_plan_subdimension_gd.py "<nombre_subdimension>" "<nivel_madurez>"
    
    Ejemplo:
    python generar_plan_subdimension_gd.py "Organización" "Basico"
    python generar_plan_subdimension_gd.py "Arquitectura" "Medio"

FLUJO:
1. Recibe subdimensión y nivel de madurez como argumentos
2. Lee datos de esa combinación desde PostgreSQL
3. Genera plan PTD con LLM (transición de nivel)
4. Genera indicador de resultado
5. Parsea el plan
6. Elimina plan antiguo (Agente Maestro) si existe
7. Inserta nuevo plan en PostgreSQL
"""

import os
import sys
import psycopg2
import uuid
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Agregar el directorio padre al path para importar services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.tracked_llm import create_tracked_llm

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

# Generar ID único para esta ejecución
GRUPO_PROCESOS = f"subscript_gd_{uuid.uuid4().hex[:12]}"

# LLM con tracking automático (se inicializará después)
llm = None

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
    """Elimina los registros antiguos de un plan específico de Gobernanza"""
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
    """Inserta un registro (actividad o hito) en la base de datos"""
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
        datos_fila['nivel_madurez'],
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

def leer_datos_subdimension(conn, nombre_subdimension, nivel_madurez):
    """
    Lee los datos de UNA subdimensión específica con su nivel de madurez desde PostgreSQL
    
    Args:
        conn: Conexión a PostgreSQL
        nombre_subdimension: Nombre de la subdimensión a buscar
        nivel_madurez: Nivel de madurez (Insuficiente, Basico, Medio)
        
    Returns:
        Dict con los datos de la subdimensión o None si no existe
    """
    print("\n" + "="*80)
    print(f"📂 LEYENDO DATOS DE SUBDIMENSIÓN: {nombre_subdimension} - Nivel: {nivel_madurez}")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
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
      AND Subdimension = %s
      AND Nivel_de_madurez = %s
    LIMIT 1
    """
    
    try:
        cursor.execute(sql, (nombre_subdimension, nivel_madurez))
        fila = cursor.fetchone()
        
        if not fila:
            print(f"❌ No se encontraron datos para '{nombre_subdimension}' con nivel '{nivel_madurez}'")
            cursor.close()
            return None
        
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
            'n_pregunta': None,
            'preguntas_condensadas': 'Preguntas del Marco MGDE respondidas negativamente',
            'nombre_iniciativa': fila[6]
        }
        
        cursor.close()
        
        print(f"✅ Datos leídos exitosamente:")
        print(f"   → Dimensión: {subdimension_data['dimension']}")
        print(f"   → Subdimensión: {subdimension_data['subdimension']}")
        print(f"   → Nivel: {subdimension_data['nivel_madurez']}")
        print(f"   → Brecha: {subdimension_data['brecha'][:100]}...")
        print()
        
        return subdimension_data
        
    except Exception as e:
        print(f"❌ Error leyendo subdimensión: {e}")
        cursor.close()
        raise

# ============================================================================
# FUNCIONES DE GENERACIÓN CON LLM
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
    """Genera un plan PTD usando el LLM para Gobernanza de Datos"""
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
5. **📈 PROGRESIÓN INCREMENTAL OBLIGATORIA**:
   - Si estás generando plan para nivel **{nivel_madurez} → {nivel_siguiente}**, asume que YA SE COMPLETARON las actividades de niveles anteriores
   - **PROHIBIDO repetir actividades de niveles previos**
   - Cada nivel debe CONSTRUIR sobre el anterior
6. **🔧 ENFOQUE 100% TÉCNICO**:
   - **LA ÚLTIMA ACTIVIDAD/HITO DEBE ALCANZAR EL NIVEL SIGUIENTE**
   - **PROHIBIDO incluir**: capacitaciones, evaluaciones, auditorías, monitoreo post-implementación

**🚨 REGLAS DE ESPECIFICIDAD OBLIGATORIAS**:
1. **CADA actividad debe tener entre 12-25 palabras** (NO menos de 12)
2. **CADA hito debe tener entre 10-20 palabras** (NO menos de 10)
3. **OBLIGATORIO especificar**: QUÉ, DÓNDE, CÓMO técnicamente

**FORMATO DE SALIDA REQUERIDO**:
```
Actividad: [Actividad 1.1]
Actividad: [Actividad 1.2]
Actividad: [Actividad 1.3]
Hito: [Descripción del hito 1]
...
```

**CRÍTICO**: MÁXIMO 3 hitos con 9-12 actividades total
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
    
    # Limpiar plan
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
    """Genera un indicador cualitativo de resultado para Gobernanza de Datos"""
    nivel_siguiente = determinar_nivel_siguiente(datos_subdimension['nivel_madurez'])
    
    print("🔄 Generando indicador de resultado...")
    
    template = """
Eres un experto en diseño de indicadores de resultado para planes de Gobernanza de Datos del gobierno chileno (Marco MGDE).

**CONTEXTO**:
- Subdimensión MGDE: {subdimension}
- Nivel ACTUAL: {nivel_actual}
- Nivel OBJETIVO: {nivel_objetivo}
- Plan: {plan}

**INDICADOR DE RESULTADO - CUALITATIVO**:
Debe describir el estado de madurez alcanzado, NO una medición.

**ESTRUCTURA**: [Capacidad MGDE] + [Estado de madurez] + [Contexto nivel {nivel_objetivo}]

**VERBOS POR NIVEL**:
- Basico: "establecido", "formalizado", "definido"
- Medio: "operativo", "implementado", "aplicado"
- Avanzado: "optimizado", "consolidado", "institucionalizado"

**REGLAS**:
- Máximo 150 caracteres
- PROHIBIDO porcentajes/números
- OBLIGATORIO verbo de estado apropiado al nivel

**GENERA EL INDICADOR CUALITATIVO**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "subdimension": datos_subdimension['subdimension'],
        "nivel_actual": datos_subdimension['nivel_madurez'],
        "nivel_objetivo": nivel_siguiente,
        "plan": plan_generado
    })
    
    indicador = response.content.strip().strip('"').strip("'")
    if indicador.endswith('.'):
        indicador = indicador[:-1]
    
    print(f"✅ Indicador de resultado: {indicador}\n")
    
    return indicador

def parsear_plan_a_registros(plan_texto):
    """Parsea el plan generado y extrae actividades e hitos"""
    if not plan_texto or str(plan_texto).strip() == '':
        return []
    
    elementos = []
    lineas = str(plan_texto).strip().split('\n')
    numero = 1
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        
        if linea.startswith('Actividad:'):
            tipo = 'Actividad'
            descripcion = linea.replace('Actividad:', '').strip()
        elif linea.startswith('Hito:'):
            tipo = 'Hito'
            descripcion = linea.replace('Hito:', '').strip()
        else:
            if elementos:
                elementos[-1] = (elementos[-1][0], elementos[-1][1], elementos[-1][2] + ' ' + linea)
            continue
        
        elementos.append((numero, tipo, descripcion))
        numero += 1
    
    return elementos

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main(nombre_subdimension, nivel_madurez):
    """Función principal que ejecuta el flujo completo para UNA subdimensión con nivel de madurez"""
    global llm, GRUPO_PROCESOS
    
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLAN PTD - SUBDIMENSIÓN + NIVEL ESPECÍFICOS")
    print("   Gobernanza de Datos (MGDE) → PostgreSQL")
    print("="*80)
    print(f"📌 Subdimensión: {nombre_subdimension}")
    print(f"📌 Nivel de Madurez: {nivel_madurez}")
    print(f"🔍 ID de grupo de procesos: {GRUPO_PROCESOS}")
    print("="*80 + "\n")
    
    # Inicializar LLM con tracking
    llm = create_tracked_llm(
        model="gpt-4o",
        temperature=0.3,
        app_name="PMG",
        grupo_procesos=GRUPO_PROCESOS,
        track_enabled=True
    )
    
    # Paso 0: Cargar SuperPrompt
    print("📖 Cargando SuperPrompt...")
    superprompt = cargar_superprompt()
    print("✅ SuperPrompt cargado\n")
    
    # Conectar a base de datos
    print("🔌 Conectando a PostgreSQL...")
    conn = conectar_db()
    print(f"✅ Conectado a: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}\n")
    
    conn.autocommit = False
    
    try:
        # Paso 1: Leer datos de la subdimensión con nivel
        datos_subdimension = leer_datos_subdimension(conn, nombre_subdimension, nivel_madurez)
        
        if not datos_subdimension:
            print("\n❌ No se pudo continuar. Combinación subdimensión-nivel no existe.")
            print("\n💡 Combinaciones disponibles:")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT Subdimension, Nivel_de_madurez
                FROM ptd_planes
                WHERE Dimension = 'Gobernanza de datos'
                  AND Nivel_de_madurez IS NOT NULL
                ORDER BY Subdimension, Nivel_de_madurez
            """)
            for subdim, nivel in cursor.fetchall():
                print(f"   • {subdim} - {nivel}")
            cursor.close()
            conn.close()
            return
        
        # Paso 2: Generar plan PTD
        plan_generado = generar_plan_ptd(datos_subdimension, superprompt)
        
        # Paso 3: Generar indicador de resultado
        indicador_resultado = generar_indicador_resultado(datos_subdimension, plan_generado)
        
        # Paso 4: Parsear plan
        print("🔄 Parseando plan...")
        elementos = parsear_plan_a_registros(plan_generado)
        
        if not elementos:
            print(f"⚠️  Plan vacío después de parsear. Abortando.")
            conn.close()
            return
        
        print(f"✅ Plan parseado: {len(elementos)} elementos")
        actividades_count = sum(1 for e in elementos if e[1] == 'Actividad')
        hitos_count = sum(1 for e in elementos if e[1] == 'Hito')
        print(f"   → {actividades_count} Actividades")
        print(f"   → {hitos_count} Hitos\n")
        
        # Paso 5: Eliminar plan antiguo
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
            print(f"ℹ️  No se encontró plan antiguo")
        
        # Paso 6: Insertar nuevo plan
        print("\n💾 Insertando nuevo plan en base de datos...")
        
        datos_fila = {
            'dimension': datos_subdimension['dimension'],
            'subdimension': datos_subdimension['subdimension'],
            'instrumento': datos_subdimension['instrumento'],
            'indicador': datos_subdimension['indicador'],
            'brecha': datos_subdimension['brecha'],
            'nivel_madurez': datos_subdimension['nivel_madurez'],
            'iniciativa': datos_subdimension['iniciativa'],
            'objetivo_iniciativa': datos_subdimension['objetivo_iniciativa'],
            'autor': 'Agente Maestro',
            'indicador_proceso': datos_subdimension['indicador_proceso'],
            'indicador_resultado': indicador_resultado
        }
        
        for numero, tipo, descripcion in elementos:
            insertar_registro(conn, datos_fila, numero, tipo, descripcion)
        
        conn.commit()
        
        print(f"✅ Plan insertado exitosamente:")
        print(f"   → Plan antiguo: {registros_eliminados} registros eliminados")
        print(f"   → Plan nuevo: {len(elementos)} registros insertados")
        
        # Verificación
        print("\n🔍 Verificando plan en base de datos...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Tipo, COUNT(*) as total
            FROM ptd_planes
            WHERE Dimension = %s
              AND Subdimension = %s
              AND Nivel_de_madurez = %s
              AND Autor = 'Agente Maestro'
            GROUP BY Tipo
            ORDER BY total DESC
        """, (datos_subdimension['dimension'], datos_subdimension['subdimension'], datos_subdimension['nivel_madurez']))
        
        print(f"\n📊 Registros en BD para '{nombre_subdimension}' ({nivel_madurez}):")
        for tipo, total in cursor.fetchall():
            print(f"   • {tipo}: {total} registros")
        
        cursor.close()
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error procesando subdimensión: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("\n" + "="*80)
        print("❌ USO INCORRECTO")
        print("="*80)
        print("\nUso correcto:")
        print('  python generar_plan_subdimension_gd.py "<nombre_subdimension>" "<nivel_madurez>"')
        print("\nEjemplos:")
        print('  python generar_plan_subdimension_gd.py "Organización" "Basico"')
        print('  python generar_plan_subdimension_gd.py "Arquitectura" "Medio"')
        print('  python generar_plan_subdimension_gd.py "Calidad de datos" "Insuficiente"')
        print("\nNiveles válidos: Insuficiente, Basico, Medio")
        print("="*80 + "\n")
        sys.exit(1)
    
    nombre_subdimension = sys.argv[1]
    nivel_madurez = sys.argv[2]
    
    # Validar nivel de madurez
    niveles_validos = ['Insuficiente', 'Basico', 'Medio', 'Avanzado']
    if nivel_madurez not in niveles_validos:
        print(f"\n❌ Nivel de madurez inválido: '{nivel_madurez}'")
        print(f"Niveles válidos: {', '.join(niveles_validos)}\n")
        sys.exit(1)
    
    try:
        main(nombre_subdimension, nivel_madurez)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
