"""
Subscript: Generación de Plan PTD para UNA Subdimensión de Calidad Web
Procesa una subdimensión + instrumento específicos desde PostgreSQL → Genera plan con LLM → Actualiza PostgreSQL
Fecha: 2025-11-05

USO:
    python generar_plan_subdimension_cw.py "<nombre_subdimension>" "<instrumento>"
    
    Ejemplo:
    python generar_plan_subdimension_cw.py "Accesibilidad web" "Instrumento de evaluación de calidad para sitios web"
    python generar_plan_subdimension_cw.py "Usabilidad" "Instrumento de evaluación de calidad para servicios digitales transaccionales"

LÓGICA ESPECIAL CALIDAD WEB:
- Cada pregunta genera UNA actividad y UN hito
- Cuando cambia el "Indicador", se inserta el hito de la fila anterior
- Contador N_Actividad_Hito secuencial para toda la subdimensión

FLUJO:
1. Recibe subdimensión e instrumento como argumentos
2. Lee preguntas de esa combinación desde PostgreSQL
3. Por cada pregunta: genera actividad + hito con LLM
4. Genera indicador de resultado (subdimensión)
5. Elimina plan antiguo (Agente Maestro) si existe
6. Inserta nuevo plan con lógica especial de hitos
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

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'ptd_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY no encontrada en .env")

# Generar ID único para esta ejecución
GRUPO_PROCESOS = f"subscript_cw_{uuid.uuid4().hex[:12]}"

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

def eliminar_plan_antiguo(conn, dimension, subdimension, instrumento, autor):
    """Elimina los registros antiguos de un plan específico de Calidad Web"""
    cursor = conn.cursor()
    
    sql = """
    DELETE FROM ptd_planes
    WHERE Dimension = %s
      AND Subdimension = %s
      AND Instrumento = %s
      AND Autor = %s
    """
    
    try:
        cursor.execute(sql, (dimension, subdimension, instrumento, autor))
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
        None,  # Nivel_de_madurez (NULL para Calidad Web)
        datos_fila['n_pregunta'],
        datos_fila['pregunta'],
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
# FUNCIONES DE LECTURA
# ============================================================================

def leer_preguntas_subdimension(conn, nombre_subdimension, instrumento):
    """
    Lee las preguntas de una subdimensión + instrumento específicos
    
    Returns:
        Lista de diccionarios con los datos de cada pregunta
    """
    print("\n" + "="*80)
    print(f"📂 LEYENDO PREGUNTAS DESDE POSTGRESQL")
    print(f"   Subdimensión: {nombre_subdimension}")
    print(f"   Instrumento: {instrumento}")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
    sql = """
    SELECT DISTINCT
        Dimension,
        Subdimension,
        Instrumento,
        Indicador,
        Brecha,
        N_Pregunta,
        Pregunta,
        Iniciativa,
        Objetivo_Iniciativa,
        Indicador_Proceso
    FROM ptd_planes
    WHERE Dimension = 'Calidad web y servicios digitales'
      AND Subdimension = %s
      AND Instrumento = %s
      AND N_Pregunta IS NOT NULL
    ORDER BY Indicador, N_Pregunta
    """
    
    try:
        cursor.execute(sql, (nombre_subdimension, instrumento))
        filas = cursor.fetchall()
        
        if not filas:
            cursor.close()
            return []
        
        preguntas = []
        for fila in filas:
            pregunta_data = {
                'dimension': fila[0],
                'subdimension': fila[1],
                'instrumento': fila[2],
                'indicador': fila[3],
                'brecha': fila[4],
                'n_pregunta': fila[5],
                'pregunta': fila[6],
                'iniciativa': fila[7],
                'objetivo_iniciativa': fila[8],
                'indicador_proceso': fila[9]
            }
            preguntas.append(pregunta_data)
        
        cursor.close()
        
        print(f"📊 Total preguntas leídas: {len(preguntas)}\n")
        
        return preguntas
        
    except Exception as e:
        print(f"❌ Error leyendo preguntas: {e}")
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

def generar_actividad_para_pregunta(datos_pregunta, superprompt):
    """Genera UNA actividad que resuelva una pregunta específica de Calidad Web"""
    template = """
{superprompt}

## TAREA: Generar ACTIVIDAD para Pregunta de Calidad Web

### Contexto del Indicador
- **Dimensión**: {dimension}
- **Subdimensión**: {subdimension}
- **Instrumento**: {instrumento}
- **Indicador**: {indicador}
- **Iniciativa**: {iniciativa}

### Pregunta a Resolver
**Pregunta #{n_pregunta}**: {pregunta}
**Respuesta Actual**: NO (no cumple)

### Brecha Identificada
{brecha}

## INSTRUCCIONES ESPECÍFICAS
1. Resuelva específicamente la pregunta planteada
2. Permita pasar de "NO cumple" a "SÍ cumple"
3. Sea concreta, medible y orientada a mejorar la calidad web
4. Tenga entre 12-25 palabras (NO menos de 12)

### Formato de Salida
Responde ÚNICAMENTE con el texto de la actividad, sin prefijos, sin "Actividad:", sin numeración.

**RESPONDE SOLO CON EL TEXTO DE LA ACTIVIDAD**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "superprompt": superprompt,
        "dimension": datos_pregunta['dimension'],
        "subdimension": datos_pregunta['subdimension'],
        "instrumento": datos_pregunta['instrumento'],
        "indicador": datos_pregunta['indicador'],
        "brecha": datos_pregunta['brecha'],
        "n_pregunta": datos_pregunta['n_pregunta'],
        "pregunta": datos_pregunta['pregunta'],
        "iniciativa": datos_pregunta['iniciativa'],
        "objetivo_iniciativa": datos_pregunta['objetivo_iniciativa'],
        "indicador_proceso": datos_pregunta['indicador_proceso']
    })
    
    actividad = response.content.strip()
    actividad = actividad.replace('Actividad:', '').strip()
    actividad = actividad.strip('"').strip("'")
    
    return actividad

def generar_hito_para_indicador(indicador, datos_pregunta, superprompt):
    """Genera UN hito que permita cumplir con un indicador completo"""
    template = """
{superprompt}

## TAREA: Generar HITO para Indicador de Calidad Web

### Contexto del Indicador
- **Indicador**: {indicador}
- **Subdimensión**: {subdimension}
- **Brecha**: {brecha}

## INSTRUCCIONES ESPECÍFICAS
1. Sea un ENTREGABLE CONCRETO Y TANGIBLE
2. Sea ESPECÍFICO para este indicador "{indicador}"
3. Tenga entre 10-20 palabras (NO menos de 10)
4. EVITAR frases genéricas o porcentajes

### Formato de Salida
Responde ÚNICAMENTE con el texto del hito, sin prefijos, sin "Hito:".

**RESPONDE SOLO CON EL TEXTO DEL HITO**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "superprompt": superprompt,
        "dimension": datos_pregunta['dimension'],
        "subdimension": datos_pregunta['subdimension'],
        "instrumento": datos_pregunta['instrumento'],
        "indicador": indicador,
        "brecha": datos_pregunta['brecha'],
        "iniciativa": datos_pregunta['iniciativa'],
        "objetivo_iniciativa": datos_pregunta['objetivo_iniciativa']
    })
    
    hito = response.content.strip()
    hito = hito.replace('Hito:', '').strip()
    hito = hito.strip('"').strip("'")
    
    return hito

def generar_indicador_resultado_subdimension(subdimension, dimension):
    """Genera un indicador cualitativo de resultado para UNA SUBDIMENSIÓN completa"""
    template = """
Eres un experto en diseño de indicadores de resultado para Calidad Web y Servicios Digitales.

**CONTEXTO**:
- Dimensión: {dimension}
- Subdimensión: {subdimension}

**INDICADOR DE RESULTADO - CUALITATIVO**:
Debe describir el ESTÁNDAR DE CALIDAD logrado.

**ESTRUCTURA**: [Aspecto calidad web] + [Estado consolidación] + [Contexto institucional]

**VERBOS PERMITIDOS**: consolidado, establecido, institucionalizado, implementado, integrado

**REGLAS**:
- Máximo 150 caracteres
- PROHIBIDO porcentajes/números
- OBLIGATORIO mencionar aspecto específico de "{subdimension}"

**GENERA EL INDICADOR CUALITATIVO**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "subdimension": subdimension,
        "dimension": dimension
    })
    
    indicador = response.content.strip().strip('"').strip("'")
    if indicador.endswith('.'):
        indicador = indicador[:-1]
    
    return indicador

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main(nombre_subdimension, instrumento):
    """Función principal que ejecuta el flujo completo para UNA subdimensión + instrumento"""
    global llm, GRUPO_PROCESOS
    
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLAN PTD - SUBDIMENSIÓN + INSTRUMENTO ESPECÍFICOS")
    print("   Calidad Web y Servicios Digitales → PostgreSQL")
    print("="*80)
    print(f"📌 Subdimensión: {nombre_subdimension}")
    print(f"📌 Instrumento: {instrumento}")
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
        # Paso 1: Leer preguntas de la subdimensión + instrumento
        preguntas = leer_preguntas_subdimension(conn, nombre_subdimension, instrumento)
        
        if not preguntas:
            print(f"\n❌ No se encontraron preguntas para '{nombre_subdimension}' con instrumento '{instrumento}'")
            print("\n💡 Combinaciones disponibles:")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT Subdimension, Instrumento
                FROM ptd_planes
                WHERE Dimension = 'Calidad web y servicios digitales'
                  AND N_Pregunta IS NOT NULL
                ORDER BY Subdimension, Instrumento
            """)
            for subdim, inst in cursor.fetchall():
                print(f"   • {subdim}")
                print(f"     → {inst}")
            cursor.close()
            conn.close()
            return
        
        # Paso 2: Generar indicador de resultado para la subdimensión
        print("🔄 Generando indicador de resultado para subdimensión...")
        dimension = preguntas[0]['dimension']
        indicador_resultado = generar_indicador_resultado_subdimension(nombre_subdimension, dimension)
        print(f"✅ Indicador de resultado: {indicador_resultado}\n")
        
        # Paso 3: Generar actividades e hitos
        print("🔄 Generando actividades e hitos...\n")
        
        indicador_anterior = None
        actividades_generadas = []
        hitos_generados = {}
        
        for pregunta in preguntas:
            indicador_actual = pregunta['indicador']
            
            # Generar actividad
            actividad = generar_actividad_para_pregunta(pregunta, superprompt)
            actividades_generadas.append({
                'pregunta_data': pregunta,
                'actividad': actividad,
                'indicador': indicador_actual
            })
            
            # Si cambia el indicador, generar nuevo hito
            if indicador_actual != indicador_anterior:
                if indicador_actual not in hitos_generados:
                    hito = generar_hito_para_indicador(indicador_actual, pregunta, superprompt)
                    hitos_generados[indicador_actual] = hito
                    print(f"   ✅ Hito generado para indicador '{indicador_actual}': {hito[:60]}...")
                
                indicador_anterior = indicador_actual
        
        print(f"\n✅ Total actividades generadas: {len(actividades_generadas)}")
        print(f"✅ Total hitos únicos generados: {len(hitos_generados)}\n")
        
        # Paso 4: Eliminar plan antiguo
        print("🗑️  Verificando y eliminando plan antiguo...")
        registros_eliminados = eliminar_plan_antiguo(
            conn,
            dimension,
            nombre_subdimension,
            instrumento,
            'Agente Maestro'
        )
        
        if registros_eliminados > 0:
            print(f"✅ Plan antiguo eliminado: {registros_eliminados} registros")
        else:
            print(f"ℹ️  No se encontró plan antiguo")
        
        # Paso 5: Insertar nuevo plan con lógica especial
        print("\n💾 Insertando nuevo plan con lógica especial de Calidad Web...")
        
        indicador_anterior = None
        hito_pendiente = None
        datos_hito_pendiente = None
        n_secuencial = 0
        registros_insertados = 0
        
        for item in actividades_generadas:
            pregunta_data = item['pregunta_data']
            actividad = item['actividad']
            indicador_actual = item['indicador']
            
            # Construir datos_fila
            datos_fila = {
                'dimension': pregunta_data['dimension'],
                'subdimension': pregunta_data['subdimension'],
                'instrumento': pregunta_data['instrumento'],
                'indicador': pregunta_data['indicador'],
                'brecha': pregunta_data['brecha'],
                'n_pregunta': pregunta_data['n_pregunta'],
                'pregunta': pregunta_data['pregunta'],
                'iniciativa': pregunta_data['iniciativa'],
                'objetivo_iniciativa': pregunta_data['objetivo_iniciativa'],
                'autor': 'Agente Maestro',
                'indicador_proceso': pregunta_data['indicador_proceso'],
                'indicador_resultado': indicador_resultado
            }
            
            # Insertar hito pendiente si cambió el indicador
            if indicador_actual != indicador_anterior and hito_pendiente and datos_hito_pendiente:
                n_secuencial += 1
                insertar_registro(conn, datos_hito_pendiente, n_secuencial, 'Hito', hito_pendiente)
                registros_insertados += 1
            
            # Insertar actividad
            n_secuencial += 1
            insertar_registro(conn, datos_fila, n_secuencial, 'Actividad', actividad)
            registros_insertados += 1
            
            # Guardar hito para insertar cuando cambie el indicador
            hito_pendiente = hitos_generados[indicador_actual]
            datos_hito_pendiente = datos_fila.copy()
            indicador_anterior = indicador_actual
        
        # Insertar el último hito pendiente
        if hito_pendiente and datos_hito_pendiente:
            n_secuencial += 1
            insertar_registro(conn, datos_hito_pendiente, n_secuencial, 'Hito', hito_pendiente)
            registros_insertados += 1
        
        # Commit
        conn.commit()
        
        print(f"✅ Plan completado:")
        print(f"   → Plan antiguo: {registros_eliminados} registros eliminados")
        print(f"   → Plan nuevo: {registros_insertados} registros insertados")
        
        # Verificación
        print("\n🔍 Verificando plan en base de datos...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Tipo, COUNT(*) as total
            FROM ptd_planes
            WHERE Dimension = %s
              AND Subdimension = %s
              AND Instrumento = %s
              AND Autor = 'Agente Maestro'
            GROUP BY Tipo
            ORDER BY total DESC
        """, (dimension, nombre_subdimension, instrumento))
        
        print(f"\n📊 Registros en BD para '{nombre_subdimension}':")
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
        print('  python generar_plan_subdimension_cw.py "<subdimension>" "<instrumento>"')
        print("\nEjemplos:")
        print('  python generar_plan_subdimension_cw.py "Accesibilidad web" "Instrumento de evaluación de calidad para sitios web"')
        print('  python generar_plan_subdimension_cw.py "Usabilidad" "Instrumento de evaluación de calidad para servicios digitales transaccionales"')
        print("\nInstrumentos comunes:")
        print('  • "Instrumento de evaluación de calidad para sitios web"')
        print('  • "Instrumento de evaluación de calidad para servicios digitales transaccionales"')
        print("="*80 + "\n")
        sys.exit(1)
    
    nombre_subdimension = sys.argv[1]
    instrumento = sys.argv[2]
    
    try:
        main(nombre_subdimension, instrumento)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
