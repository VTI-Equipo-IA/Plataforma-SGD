"""
Script Unificado: Generación e Inserción de Planes PTD - Calidad Web
Procesa subdimensiones desde PostgreSQL → Genera planes con LLM → Actualiza PostgreSQL
Fecha: 2025-11-05

LÓGICA ESPECIAL PARA CALIDAD WEB:
- Cada pregunta genera UNA actividad y UN hito (en la misma celda)
- Un plan completo está asociado a UNA subdimensión
- Cuando cambia el "Indicador", se inserta el hito de la fila anterior
- Cuando cambia la "Subdimensión", se reinicia el contador N_Actividad_Hito

FLUJO:
1. Lee preguntas desde PostgreSQL (por Dimension, Subdimension, Instrumento)
2. Por cada pregunta, genera actividad + hito con LLM
3. Genera indicador de resultado (a nivel de subdimensión)
4. Elimina plan antiguo (Agente Maestro) si existe
5. Inserta nuevo plan con lógica especial de hitos
6. Repite para todas las subdimensiones
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
GRUPO_PROCESOS = f"maestro_cw_{uuid.uuid4().hex[:12]}"
print(f"🔍 ID de grupo de procesos: {GRUPO_PROCESOS}")

# LLM con tracking automático
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

def eliminar_plan_antiguo(conn, dimension, subdimension, instrumento, autor):
    """
    Elimina los registros antiguos de un plan específico de Calidad Web
    
    Args:
        conn: Conexión a PostgreSQL
        dimension: Dimensión del plan
        subdimension: Subdimensión del plan
        instrumento: Instrumento del plan
        autor: Autor del plan ('Agente Maestro' o 'Comite')
        
    Returns:
        Número de registros eliminados
    """
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
# FUNCIONES DE LECTURA DE DATOS DE ENTRADA
# ============================================================================

def leer_preguntas_desde_db(conn):
    """
    Lee las preguntas de Calidad Web directamente desde PostgreSQL
    Busca por Dimension, Subdimension, Instrumento para obtener planes únicos
    
    Args:
        conn: Conexión a PostgreSQL
        
    Returns:
        Lista de diccionarios con los datos de cada pregunta
    """
    print("\n" + "="*80)
    print("📂 LEYENDO PREGUNTAS DESDE POSTGRESQL")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
    # Query para obtener todas las preguntas con sus datos
    # Ordenamos por Subdimension, Indicador, N_Pregunta
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
      AND N_Pregunta IS NOT NULL
    ORDER BY Subdimension, Indicador, N_Pregunta
    """
    
    try:
        cursor.execute(sql)
        filas = cursor.fetchall()
        
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
        
        print(f"📊 Total preguntas leídas: {len(preguntas)}")
        
        # Mostrar agrupación por subdimensión
        subdimensiones_unicas = {}
        for p in preguntas:
            key = f"{p['subdimension']}"
            if key not in subdimensiones_unicas:
                subdimensiones_unicas[key] = 0
            subdimensiones_unicas[key] += 1
        
        print(f"\n📋 Preguntas por subdimensión:")
        for subdim, count in subdimensiones_unicas.items():
            print(f"   • {subdim}: {count} preguntas")
        
        print()
        
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
    """
    Genera UNA actividad que resuelva una pregunta específica de Calidad Web
    
    Args:
        datos_pregunta: Dict con datos de la pregunta
        superprompt: Texto del SuperPrompt
        
    Returns:
        String con la actividad
    """
    template = """
{superprompt}

## TAREA: Generar ACTIVIDAD para Pregunta de Calidad Web

### Contexto del Indicador
- **Dimensión**: {dimension}
- **Subdimensión**: {subdimension}
- **Instrumento**: {instrumento}
- **Indicador**: {indicador}
- **Iniciativa**: {iniciativa}
- **Objetivo de Iniciativa**: {objetivo_iniciativa}
- **Indicador Proceso**: {indicador_proceso}

### Pregunta a Resolver
**Pregunta #{n_pregunta}**: {pregunta}

**Respuesta Actual**: NO (no cumple)

### Brecha Identificada
{brecha}

## INSTRUCCIONES ESPECÍFICAS

Debes generar **UNA SOLA ACTIVIDAD** que:
1. Resuelva específicamente la pregunta planteada
2. Permita pasar de "NO cumple" a "SÍ cumple" con esa pregunta
3. Sea concreta, medible y orientada a mejorar la calidad web
4. Considere el indicador al que pertenece ({indicador})
5. Esté alineada con la brecha y el objetivo de la iniciativa
6. Tenga entre 12-25 palabras (NO menos de 12)

### Formato de Salida
Responde ÚNICAMENTE con el texto de la actividad, sin prefijos, sin "Actividad:", sin numeración, sin explicaciones adicionales.

**Ejemplo de respuesta correcta**:
Actualizar el encabezado y pie de página de todas las secciones del sitio web para incluir de manera visible el nombre oficial de la institución y el logo corporativo

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
    """
    Genera UN hito que permita cumplir con un indicador completo
    
    Args:
        indicador: Nombre del indicador
        datos_pregunta: Dict con datos de la pregunta
        superprompt: Texto del SuperPrompt
        
    Returns:
        String con el hito
    """
    template = """
{superprompt}

## TAREA: Generar HITO para Indicador de Calidad Web

### Contexto del Indicador
- **Dimensión**: {dimension}
- **Subdimensión**: {subdimension}
- **Instrumento**: {instrumento}
- **Indicador**: {indicador}
- **Iniciativa**: {iniciativa}
- **Objetivo de Iniciativa**: {objetivo_iniciativa}

### Brecha General
{brecha}

## INSTRUCCIONES ESPECÍFICAS

Debes generar **UN SOLO HITO ÚNICO Y ESPECÍFICO** para el indicador "{indicador}" que:

1. Sea un **ENTREGABLE CONCRETO Y TANGIBLE** (NO un porcentaje de logro)
2. Sea **ESPECÍFICO Y ÚNICO** para este indicador (no usar frases genéricas)
3. Represente algo que se puede completar y verificar como terminado
4. Use verbos de logro como: "Implementar", "Establecer", "Crear", "Desarrollar", "Configurar", "Desplegar"
5. Tenga entre 10-20 palabras (NO menos de 10)
6. **EVITAR** frases genéricas que apliquen a cualquier indicador
7. **EVITAR** frases con porcentajes: "Asegurar que el X%", "Lograr el X%"

### REGLAS CRÍTICAS:
- El hito debe ser TAN ESPECÍFICO que solo aplique al indicador "{indicador}"
- Debe ser un PRODUCTO/RESULTADO tangible, no un proceso genérico

### Formato de Salida
Responde ÚNICAMENTE con el texto del hito, sin prefijos, sin "Hito:", sin numeración, sin explicaciones adicionales.

**RESPONDE SOLO CON EL TEXTO DEL HITO (debe ser ESPECÍFICO para "{indicador}", NO genérico)**:
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
    """
    Genera un indicador cualitativo de resultado para UNA SUBDIMENSIÓN completa
    
    Args:
        subdimension: Nombre de la subdimensión
        dimension: Dimensión principal
        
    Returns:
        String con el indicador de resultado
    """
    template = """
Eres un experto en diseño de indicadores de resultado para planes de transformación digital del gobierno chileno, 
específicamente en el área de **Calidad Web y Servicios Digitales**.

**CONTEXTO**:
- Dimensión: {dimension}
- Subdimensión de Calidad Web: {subdimension}

**INDICADOR DE RESULTADO - ENFOQUE CUALITATIVO**:

El indicador de resultado debe ser CUALITATIVO y describir el ESTÁNDAR DE CALIDAD logrado.

**CARACTERÍSTICAS DEL INDICADOR DE RESULTADO**:
1. **Cualitativo**: Describe el estándar de calidad alcanzado, NO una medición
2. **De Impacto**: Refleja la transformación en la calidad del sitio web institucional
3. **Integral**: Abarca el propósito completo de la subdimensión de calidad web
4. **Institucional**: Refleja la calidad web como capacidad institucional consolidada

**ESTRUCTURA OBLIGATORIA**:
[Aspecto de calidad web] + [Estado de consolidación] + [Contexto institucional]

**VERBOS/ESTADOS PERMITIDOS**:
- consolidado, establecido, institucionalizado, implementado, integrado
- operativo, funcional, adoptado, normalizado, estandarizado

**REGLAS ESTRICTAS**:
- Responde SOLO con el texto del indicador (una sola línea)
- NO incluyas explicaciones adicionales
- NO uses comillas ni puntos al final
- Máximo 150 caracteres
- **PROHIBIDO** usar porcentajes (%), números, cantidades
- **OBLIGATORIO** usar verbos de estado
- **OBLIGATORIO** mencionar el aspecto de calidad web específico de la subdimensión "{subdimension}"

**GENERA EL INDICADOR CUALITATIVO AHORA**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "subdimension": subdimension,
        "dimension": dimension
    })
    
    indicador = response.content.strip()
    indicador = indicador.strip('"').strip("'")
    if indicador.endswith('.'):
        indicador = indicador[:-1]
    
    return indicador

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Función principal que ejecuta el flujo completo para Calidad Web:
    1. Leer preguntas desde PostgreSQL
    2. Agrupar por subdimensión + instrumento
    3. Para cada grupo:
       a. Generar actividad por cada pregunta
       b. Generar hito cuando cambia indicador
       c. Generar indicador de resultado (subdimensión)
       d. Eliminar plan antiguo
       e. Insertar nuevo plan con lógica especial
    """
    print("\n" + "="*80)
    print("🚀 INICIO: GENERACIÓN E INSERCIÓN DE PLANES PTD")
    print("   Calidad Web y Servicios Digitales → PostgreSQL")
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
    
    # Paso 1: Leer preguntas desde PostgreSQL
    preguntas = leer_preguntas_desde_db(conn)
    
    # Paso 2: Agrupar preguntas por subdimensión + instrumento
    print("="*80)
    print("📊 AGRUPANDO PREGUNTAS POR SUBDIMENSIÓN + INSTRUMENTO")
    print("="*80 + "\n")
    
    grupos = {}
    for pregunta in preguntas:
        key = (pregunta['subdimension'], pregunta['instrumento'])
        if key not in grupos:
            grupos[key] = []
        grupos[key].append(pregunta)
    
    print(f"✅ Total grupos (planes únicos): {len(grupos)}\n")
    
    # Estadísticas
    total_grupos = len(grupos)
    grupos_procesados = 0
    total_registros_insertados = 0
    
    # Paso 3: Procesar cada grupo (subdimensión + instrumento)
    for idx, ((subdimension, instrumento), preguntas_grupo) in enumerate(grupos.items(), 1):
        print("\n" + "="*80)
        print(f"📋 PROCESANDO GRUPO {idx}/{total_grupos}")
        print(f"   Subdimensión: {subdimension}")
        print(f"   Instrumento: {instrumento}")
        print(f"   Total preguntas: {len(preguntas_grupo)}")
        print("="*80)
        
        try:
            # Generar indicador de resultado para la subdimensión
            print("\n🔄 Generando indicador de resultado para subdimensión...")
            dimension = preguntas_grupo[0]['dimension']
            indicador_resultado = generar_indicador_resultado_subdimension(subdimension, dimension)
            print(f"✅ Indicador de resultado: {indicador_resultado}\n")
            
            # Variables de control para lógica especial de Calidad Web
            indicador_anterior = None
            hito_actual = None
            n_secuencial = 0
            actividades_generadas = []
            hitos_generados = {}
            
            # Paso 3a: Generar actividad para cada pregunta
            print("🔄 Generando actividades e hitos...\n")
            
            for pregunta in preguntas_grupo:
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
            
            # Paso 3b: Eliminar plan antiguo si existe
            print("🗑️  Verificando y eliminando plan antiguo...")
            registros_eliminados = eliminar_plan_antiguo(
                conn,
                dimension,
                subdimension,
                instrumento,
                'Agente Maestro'
            )
            
            if registros_eliminados > 0:
                print(f"✅ Plan antiguo eliminado: {registros_eliminados} registros")
            else:
                print(f"ℹ️  No se encontró plan antiguo para eliminar")
            
            # Paso 3c: Insertar nuevo plan con lógica especial
            print("\n💾 Insertando nuevo plan con lógica especial de Calidad Web...")
            
            indicador_anterior = None
            hito_pendiente = None
            datos_hito_pendiente = None
            registros_insertados = 0
            
            for item in actividades_generadas:
                pregunta_data = item['pregunta_data']
                actividad = item['actividad']
                indicador_actual = item['indicador']
                
                # Construir datos_fila para esta actividad
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
                datos_hito_pendiente = datos_fila.copy()  # Guardar datos para el hito
                indicador_anterior = indicador_actual
            
            # Insertar el último hito pendiente
            if hito_pendiente and datos_hito_pendiente:
                n_secuencial += 1
                insertar_registro(conn, datos_hito_pendiente, n_secuencial, 'Hito', hito_pendiente)
                registros_insertados += 1
            
            # Commit del grupo
            conn.commit()
            
            grupos_procesados += 1
            total_registros_insertados += registros_insertados
            
            print(f"✅ Grupo completado:")
            print(f"   → Plan antiguo: {registros_eliminados} registros eliminados")
            print(f"   → Plan nuevo: {registros_insertados} registros insertados\n")
            
        except Exception as e:
            print(f"\n❌ Error procesando grupo '{subdimension}' ({instrumento}): {e}")
            conn.rollback()
            print("🔄 Continuando con siguiente grupo...\n")
            continue
    
    # Cerrar conexión
    conn.close()
    
    # Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"✅ Grupos procesados: {grupos_procesados}/{total_grupos}")
    print(f"✅ Total registros insertados: {total_registros_insertados}")
    print(f"📊 Promedio registros/grupo: {total_registros_insertados/grupos_procesados:.1f}" if grupos_procesados > 0 else "")
    print("="*80)
    
    # Verificación final en base de datos
    print("\n🔍 Verificando datos en PostgreSQL...")
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Contar registros por subdimensión
    cursor.execute("""
        SELECT Subdimension, COUNT(*) as total
        FROM ptd_planes
        WHERE Dimension = 'Calidad web y servicios digitales'
          AND Autor = 'Agente Maestro'
        GROUP BY Subdimension
        ORDER BY Subdimension
    """)
    
    print("\n📊 Registros por subdimensión:")
    for subdim, total in cursor.fetchall():
        print(f"   • {subdim}: {total} registros")
    
    # Contar por tipo
    cursor.execute("""
        SELECT Tipo, COUNT(*) as total
        FROM ptd_planes
        WHERE Dimension = 'Calidad web y servicios digitales'
          AND Autor = 'Agente Maestro'
        GROUP BY Tipo
        ORDER BY total DESC
    """)
    
    print("\n📊 Registros por tipo:")
    for tipo, total in cursor.fetchall():
        print(f"   • {tipo}: {total} registros")
    
    cursor.close()
    conn.close()
    
    print("\n✅ PROCESO COMPLETADO EXITOSAMENTE!\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        raise
