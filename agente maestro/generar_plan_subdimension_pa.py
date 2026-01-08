"""
Subscript: Generación de Plan PTD para UNA Subdimensión de Procedimiento Administrativo
Procesa una subdimensión específica desde PostgreSQL → Genera plan con LLM → Actualiza PostgreSQL
Fecha: 2025-11-05

USO:
    python generar_plan_subdimension_pa.py "<nombre_subdimension>"
    
    Ejemplo:
    python generar_plan_subdimension_pa.py "Autenticación"
    python generar_plan_subdimension_pa.py "Notificación"

FLUJO:
1. Recibe nombre de subdimensión como argumento
2. Lee datos de esa subdimensión desde PostgreSQL
3. Genera plan PTD con LLM
4. Genera indicador de resultado
5. Parsea el plan
6. Elimina plan antiguo (Agente Maestro) si existe
7. Inserta nuevo plan en PostgreSQL
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
GRUPO_PROCESOS = f"subscript_pa_{uuid.uuid4().hex[:12]}"

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

def eliminar_plan_antiguo(conn, dimension, subdimension, autor):
    """
    Elimina los registros antiguos de un plan específico
    
    Args:
        conn: Conexión a PostgreSQL
        dimension: Dimensión del plan
        subdimension: Subdimensión del plan
        autor: Autor del plan ('Agente Maestro' o 'Comite')
        
    Returns:
        Número de registros eliminados
    """
    cursor = conn.cursor()
    
    sql = """
    DELETE FROM ptd_planes
    WHERE Dimension = %s
      AND Subdimension = %s
      AND Autor = %s
    """
    
    try:
        cursor.execute(sql, (dimension, subdimension, autor))
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
        None,  # Nivel_de_madurez (NULL para Procedimiento Administrativo)
        None,  # N_Pregunta (NULL para PA)
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

def leer_datos_subdimension(conn, nombre_subdimension):
    """
    Lee los datos de UNA subdimensión específica desde PostgreSQL
    
    Args:
        conn: Conexión a PostgreSQL
        nombre_subdimension: Nombre de la subdimensión a buscar
        
    Returns:
        Dict con los datos de la subdimensión o None si no existe
    """
    print("\n" + "="*80)
    print(f"📂 LEYENDO DATOS DE SUBDIMENSIÓN: {nombre_subdimension}")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
    # Query para obtener datos de la subdimensión específica
    sql = """
    SELECT DISTINCT
        Dimension,
        Subdimension,
        Instrumento,
        Indicador,
        Brecha,
        Pregunta,
        Iniciativa,
        Objetivo_Iniciativa,
        Indicador_Proceso
    FROM ptd_planes
    WHERE Dimension = 'Procedimiento administrativo de función específica'
      AND Subdimension = %s
    LIMIT 1
    """
    
    try:
        cursor.execute(sql, (nombre_subdimension,))
        fila = cursor.fetchone()
        
        if not fila:
            print(f"❌ No se encontraron datos para la subdimensión '{nombre_subdimension}'")
            cursor.close()
            return None
        
        subdimension_data = {
            'dimension': fila[0],
            'subdimension': fila[1],
            'instrumento': fila[2],
            'indicador': fila[3],
            'brecha': fila[4],
            'pregunta': fila[5],
            'iniciativa': fila[6],
            'objetivo_iniciativa': fila[7],
            'indicador_proceso': fila[8],
            'respuesta': 'No',  # Por defecto es "No" si hay brecha
            'nombre_iniciativa': fila[6]  # Usar mismo valor que iniciativa
        }
        
        cursor.close()
        
        print(f"✅ Datos leídos exitosamente:")
        print(f"   → Dimensión: {subdimension_data['dimension']}")
        print(f"   → Subdimensión: {subdimension_data['subdimension']}")
        print(f"   → Instrumento: {subdimension_data['instrumento']}")
        print(f"   → Brecha: {subdimension_data['brecha'][:100]}...")
        print()
        
        return subdimension_data
        
    except Exception as e:
        print(f"❌ Error leyendo subdimensión: {e}")
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

def generar_plan_ptd(datos_subdimension, superprompt):
    """
    Genera un plan PTD usando el LLM
    
    Args:
        datos_subdimension: Dict con datos de la subdimensión
        superprompt: Texto del SuperPrompt
        
    Returns:
        String con el plan en formato:
        Actividad: ...
        Actividad: ...
        Hito: ...
    """
    print(f"\n{'='*80}")
    print(f"🤖 GENERANDO PLAN: {datos_subdimension['subdimension']}")
    print(f"{'='*80}\n")
    
    template = """
{superprompt}

---

## TAREA ESPECÍFICA: Generar Plan PTD para Procedimiento Administrativo

**Datos de la Subdimensión**:
- Dimensión: {dimension}
- Subdimensión: {subdimension}
- Instrumento: {instrumento}
- Indicador: {indicador}
- Brecha: {brecha}
- Pregunta: {pregunta}
- Respuesta: {respuesta}
- Iniciativa: {iniciativa}
- Objetivo de Iniciativa: {objetivo_iniciativa}
- Indicador Proceso: {indicador_proceso}
- Nombre Iniciativa: {nombre_iniciativa}

**INSTRUCCIONES CRÍTICAS**:
1. Este plan es para DESARROLLADORES - solo pasos técnicos de implementación
2. Genera SOLO 3-4 HITOS MÁXIMO (NO 7 hitos)
3. Cada hito debe tener 3-4 ACTIVIDADES técnicas
4. Total esperado: 10-16 actividades MÁXIMO
5. **ÚLTIMA ACTIVIDAD = CIERRA LA BRECHA** (NO agregar trabajo posterior)
6. Usa el formato de celda única con saltos de línea
7. SIGUE las reglas de redacción del SuperPrompt (verbos en infinitivo, perspectiva interna)

**🚨 REGLAS DE ESPECIFICIDAD OBLIGATORIAS (CRÍTICO - ELIMINAR HIPERSÍNTESIS)**:
1. **CADA actividad debe tener entre 12-25 palabras** (NO menos de 12)
2. **CADA hito debe tener entre 10-20 palabras** (NO menos de 10)
3. **PROHIBIDO usar enunciados genéricos**:
   - ❌ "Implementar sistema de autenticación"
   - ❌ "Capacitar al personal"
   - ❌ "Establecer protocolos"
4. **OBLIGATORIO especificar**:
   - QUÉ exactamente (herramienta, documento, sistema específico)
   - DÓNDE específicamente (portal, plataforma, área concreta)
   - CÓMO técnicamente (SDK, API, metodología específica)

**SOLO PARA SUBDIMENSIÓN "{subdimension}"**:
- ❌ NO mencionar otras subdimensiones
- ✅ SOLO actividades relacionadas con "{subdimension}"

**ACTIVIDADES ABSOLUTAMENTE PROHIBIDAS**:
- ❌ "Implementar sistema de monitoreo..." / "Monitorear..."
- ❌ "Optimizar..." / "Implementar mejoras de rendimiento..."
- ❌ "Formalizar el cierre..." / "Comunicar finalización..."
- ❌ "Documentar lecciones aprendidas..."
- ❌ Cualquier actividad DESPUÉS de despliegue en producción

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
Actividad: [ÚLTIMA - Certificar operatividad]
Hito: [Hito final que cierra la brecha]
```

**CRÍTICO**: 
- Las ACTIVIDADES van PRIMERO, el HITO va DESPUÉS de sus actividades
- Devuelve SOLO el plan en formato texto plano
- NO incluyas marcadores de código (```) ni explicaciones adicionales
- Cada línea debe empezar con "Hito: " o "Actividad: "
- MÁXIMO 3-4 hitos con 10-16 actividades total
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
        "pregunta": datos_subdimension['pregunta'],
        "respuesta": datos_subdimension['respuesta'],
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
    Genera un indicador cualitativo de resultado
    
    Args:
        datos_subdimension: Dict con datos de la subdimensión
        plan_generado: String con el plan PTD generado
        
    Returns:
        String con el indicador de resultado
    """
    print("🔄 Generando indicador de resultado...")
    
    template = """
Eres un experto en diseño de indicadores de resultado para planes de transformación digital del gobierno chileno.

**CONTEXTO**:
- Subdimensión PMG: {subdimension}
- Iniciativa: {iniciativa}
- Plan a medir (actividades e hitos):
{plan}

**INDICADOR DE RESULTADO - ENFOQUE CUALITATIVO**:

El indicador de resultado debe ser CUALITATIVO y describir el IMPACTO o CAMBIO logrado.

**DIFERENCIA FUNDAMENTAL**:
- ❌ **Indicador Proceso** (cuantitativo): "% de sistemas con ClaveÚnica implementada"
- ✅ **Indicador Resultado** (cualitativo): "Autenticación digital mediante ClaveÚnica consolidada como mecanismo oficial de identificación en todos los canales digitales institucionales"

**CARACTERÍSTICAS DEL INDICADOR DE RESULTADO**:
1. **Cualitativo**: Describe un estado o condición lograda, NO una medición
2. **De Impacto**: Refleja el cambio o transformación institucional alcanzada
3. **Integral**: Abarca el propósito completo del plan
4. **Verificable**: Observable aunque no sea medible numéricamente
5. **Institucional**: Refleja un cambio en la capacidad o práctica de la institución

**ESTRUCTURA OBLIGATORIA**:
[Concepto/Capacidad] + [Estado de consolidación] + [Contexto institucional]

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

**GENERA EL INDICADOR CUALITATIVO AHORA**:
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "subdimension": datos_subdimension['subdimension'],
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

def main(nombre_subdimension):
    """
    Función principal que ejecuta el flujo completo para UNA subdimensión:
    1. Leer datos de la subdimensión desde PostgreSQL
    2. Generar plan PTD con LLM
    3. Generar indicador de resultado
    4. Parsear plan
    5. Eliminar plan antiguo (Agente Maestro) si existe
    6. Insertar nuevo plan en PostgreSQL
    """
    global llm, GRUPO_PROCESOS
    
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLAN PTD - SUBDIMENSIÓN ESPECÍFICA")
    print("   Procedimiento Administrativo → PostgreSQL")
    print("="*80)
    print(f"📌 Subdimensión a procesar: {nombre_subdimension}")
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
    
    conn.autocommit = False  # Usar transacciones
    
    try:
        # Paso 1: Leer datos de la subdimensión
        datos_subdimension = leer_datos_subdimension(conn, nombre_subdimension)
        
        if not datos_subdimension:
            print("\n❌ No se pudo continuar. La subdimensión no existe en la base de datos.")
            print("\n💡 Subdimensiones disponibles:")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT Subdimension
                FROM ptd_planes
                WHERE Dimension = 'Procedimiento administrativo de función específica'
                ORDER BY Subdimension
            """)
            for (subdim,) in cursor.fetchall():
                print(f"   • {subdim}")
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
        
        # Paso 5: Eliminar plan antiguo si existe
        print("🗑️  Verificando y eliminando plan antiguo...")
        registros_eliminados = eliminar_plan_antiguo(
            conn,
            datos_subdimension['dimension'],
            datos_subdimension['subdimension'],
            'Agente Maestro'
        )
        
        if registros_eliminados > 0:
            print(f"✅ Plan antiguo eliminado: {registros_eliminados} registros")
        else:
            print(f"ℹ️  No se encontró plan antiguo para eliminar")
        
        # Paso 6: Insertar nuevo plan en PostgreSQL
        print("\n💾 Insertando nuevo plan en base de datos...")
        
        # Preparar datos comunes
        datos_fila = {
            'dimension': datos_subdimension['dimension'],
            'subdimension': datos_subdimension['subdimension'],
            'instrumento': datos_subdimension['instrumento'],
            'indicador': datos_subdimension['indicador'],
            'brecha': datos_subdimension['brecha'],
            'pregunta': datos_subdimension['pregunta'],
            'iniciativa': datos_subdimension['iniciativa'],
            'objetivo_iniciativa': datos_subdimension['objetivo_iniciativa'],
            'autor': 'Agente Maestro',
            'indicador_proceso': datos_subdimension['indicador_proceso'],
            'indicador_resultado': indicador_resultado
        }
        
        # Insertar cada elemento
        registros_insertados = 0
        for numero, tipo, descripcion in elementos:
            try:
                insertar_registro(conn, datos_fila, numero, tipo, descripcion)
                registros_insertados += 1
                print(f"   ✓ Registro {numero}/{len(elementos)}: {tipo}")
            except Exception as e:
                print(f"   ✗ Error en registro {numero}: {e}")
                raise
        
        # Commit
        print(f"\n💾 Guardando cambios en base de datos...")
        conn.commit()
        print(f"✅ Commit exitoso: {registros_insertados} registros guardados")
        
        print(f"✅ Plan insertado exitosamente:")
        print(f"   → Plan antiguo: {registros_eliminados} registros eliminados")
        print(f"   → Plan nuevo: {len(elementos)} registros insertados")
        
        # Verificación final
        print("\n🔍 Verificando plan en base de datos...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Tipo, COUNT(*) as total
            FROM ptd_planes
            WHERE Dimension = %s
              AND Subdimension = %s
              AND Autor = 'Agente Maestro'
            GROUP BY Tipo
            ORDER BY total DESC
        """, (datos_subdimension['dimension'], datos_subdimension['subdimension']))
        
        print(f"\n📊 Registros en base de datos para '{nombre_subdimension}':")
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
    # Validar argumentos
    if len(sys.argv) != 2:
        print("\n" + "="*80)
        print("❌ USO INCORRECTO")
        print("="*80)
        print("\nUso correcto:")
        print('  python generar_plan_subdimension_pa.py "<nombre_subdimension>"')
        print("\nEjemplos:")
        print('  python generar_plan_subdimension_pa.py "Autenticación"')
        print('  python generar_plan_subdimension_pa.py "Notificación"')
        print('  python generar_plan_subdimension_pa.py "Validación de documentos"')
        print("\n" + "="*80 + "\n")
        sys.exit(1)
    
    nombre_subdimension = sys.argv[1]
    
    try:
        main(nombre_subdimension)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
