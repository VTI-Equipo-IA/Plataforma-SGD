#!/usr/bin/env python3
"""
Subscript Comité: Generación de Plan PTD para UNA Subdimensión - Calidad Web
Procesa una subdimensión + instrumento específicos desde PostgreSQL → Comité debate → Actualiza PostgreSQL
Refactorizado: 2025-11-20 - Sincronizado con main_calidad_web_bd.py

USO:
    python generar_plan_subdimension_cw.py "<nombre_subdimension>" "<instrumento>"
    
    Ejemplo:
    python generar_plan_subdimension_cw.py "Accesibilidad web" "Instrumento de evaluación de calidad para sitios web"
    python generar_plan_subdimension_cw.py "Usabilidad" "Instrumento de evaluación de calidad para servicios digitales transaccionales"

LÓGICA ESPECIAL CALIDAD WEB:
- Cada pregunta genera UNA actividad (mediante debate del Comité)
- Cuando cambia el "Indicador", se genera UN hito (mediante debate del Comité)
- Contador N_Actividad_Hito secuencial para toda la subdimensión
- Se inserta el hito DESPUÉS de la última actividad de cada indicador

WORKFLOW COMPLETO:
1. Recibe subdimensión e instrumento como argumentos
2. Lee preguntas de esa combinación desde PostgreSQL
3. Genera indicador de resultado (subdimensión) con PMG
4. Por cada pregunta:
   - Genera actividad específica con debate del Comité
   - Si es nuevo indicador, genera hito con debate del Comité
5. Elimina plan antiguo (Comite) si existe
6. Inserta nuevo plan con lógica especial:
   - Actividades secuenciales
   - Hitos después de cada grupo de indicador
   - Indicador_Resultado nunca NULL (con fallback)
7. Verifica inserción en BD
"""
from __future__ import annotations
import sys, os, re, uuid
from typing import Dict, Any, List
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración PostgreSQL desde .env
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'ptd_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

TABLE = "ptd_planes"
DIM_FILTER = "Calidad web y servicios digitales"
AUTOR = "Comite"

# Generar ID único para esta ejecución
GRUPO_PROCESOS = f"comite_cw_{uuid.uuid4().hex[:12]}"

# ============================================================================
# IMPORTACIÓN DE SERVIDORES MCP
# ============================================================================

def _import_servers():
    """Importa los servidores MCP desde la ruta correcta"""
    # Añadir ruta padre al path para importar módulos comite
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Importar servidores MCP
    from mcp.servers import mcp_server_pmg as pmg_srv
    from mcp.servers import mcp_server_abogado as abo_srv
    from mcp.servers import mcp_server_implementador as imp_srv
    from mcp.servers import mcp_server_desarrollador as dev_srv
    
    return pmg_srv, abo_srv, imp_srv, dev_srv

pmg_srv, abo_srv, imp_srv, dev_srv = _import_servers()

# ============================================================================
# PATRONES Y FUNCIONES AUXILIARES
# ============================================================================

NUM_PAT = re.compile(r'^(\d+)[\.\-\)]?\s+(.+)')
RE_HITO = re.compile(r'^\**\s*(?:HITO|Hito|hito)\s+(\d+)\s*:?\s*\**', re.IGNORECASE)

def _as_text(x) -> str:
    if x is None: return ""
    if isinstance(x, list): return "\n".join(str(i).strip() for i in x if str(i).strip())
    return str(x)

def _is_hito(line: str) -> bool:
    """Verifica si una línea representa un hito"""
    if not line:
        return False
    line = line.strip()
    return bool(RE_HITO.match(line))

# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def conectar_db():
    """Establece conexión con PostgreSQL usando psycopg2"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        raise

def leer_preguntas_subdimension(conn, nombre_subdimension, instrumento):
    """
    Lee las preguntas de una subdimensión + instrumento específicos desde PostgreSQL
    
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
        Indicador_Proceso,
        Indicador_Resultado
    FROM ptd_planes
    WHERE Dimension = %s
      AND Subdimension = %s
      AND Instrumento = %s
      AND N_Pregunta IS NOT NULL
    ORDER BY Indicador, N_Pregunta
    """
    
    try:
        cursor.execute(sql, (DIM_FILTER, nombre_subdimension, instrumento))
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
                'indicador_proceso': fila[9],
                'indicador_resultado': fila[10] if len(fila) > 10 else None
            }
            preguntas.append(pregunta_data)
        
        cursor.close()
        
        print(f"📊 Total preguntas leídas: {len(preguntas)}")
        
        # Mostrar indicador_resultado previo si existe
        if preguntas and preguntas[0].get('indicador_resultado'):
            print(f"📌 Indicador resultado previo: {preguntas[0]['indicador_resultado']}")
        print()
        
        return preguntas
        
    except Exception as e:
        print(f"❌ Error leyendo preguntas: {e}")
        cursor.close()
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
    
    # Asegurar que indicador_resultado NUNCA sea NULL
    indicador_resultado = datos_fila.get('indicador_resultado')
    if not indicador_resultado or not indicador_resultado.strip():
        # Fallback: generar indicador contextual
        contexto = f"{datos_fila['subdimension']} usando {datos_fila['instrumento']}"
        indicador_resultado = f"Porcentaje de cumplimiento de {contexto} verificado"
    
    valores = (
        datos_fila['dimension'],
        datos_fila['subdimension'],
        datos_fila['instrumento'],
        datos_fila['indicador'],
        datos_fila['brecha'],
        None,  # Nivel_de_madurez (NULL para Calidad Web)
        datos_fila.get('n_pregunta'),
        datos_fila.get('pregunta'),
        datos_fila['iniciativa'],
        datos_fila['objetivo_iniciativa'],
        AUTOR,
        datos_fila['indicador_proceso'],
        indicador_resultado,
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
# FUNCIONES DE GENERACIÓN CON COMITÉ
# ============================================================================

def generar_actividad_para_pregunta_comite(datos_pregunta, hito_indicador, pmg, abo_srv, imp_srv, dev_srv):
    """
    Genera UNA actividad concreta para una pregunta usando el Comité.
    Replica la lógica de generar_actividad_con_comite del bulk processor.
    """
    contexto = (
        f"Dimensión: {datos_pregunta['dimension']}. Subdimensión: {datos_pregunta['subdimension']}. "
        f"Instrumento: {datos_pregunta['instrumento']}. Indicador: {datos_pregunta['indicador']}. "
        f"Brecha: {datos_pregunta['brecha']}. Iniciativa: {datos_pregunta['iniciativa']}. "
        f"Objetivo: {datos_pregunta['objetivo_iniciativa']}. Indicador de proceso: {datos_pregunta['indicador_proceso']}."
    )
    
    base_listado = (
        f"Pregunta #{datos_pregunta['n_pregunta']}: {datos_pregunta['pregunta']}. "
        "Generar UNA actividad concreta y medible que permita pasar de NO cumple a SÍ cumple."
    )
    
    # PMG propone actividad inicial usando el hito del indicador
    prop = pmg.generate_initial({
        "dimension": DIM_FILTER,
        "subdimension": datos_pregunta["subdimension"],
        "brecha": datos_pregunta["brecha"],
        "pregunta": datos_pregunta["pregunta"],
        "respuesta": "No",
        "listado": base_listado,
        "hitos_previos": hito_indicador,
    }) or {}
    
    listado_inicial = _as_text((prop.get("payload") or {}).get("listado", ""))
    if not listado_inicial.strip():
        listado_inicial = base_listado
    
    payload_inter = {
        "contexto_pm": contexto,
        "listado_vigente": listado_inicial,
    }
    
    A = _as_text((abo_srv.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    I = _as_text((imp_srv.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    D = _as_text((dev_srv.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    
    cons = pmg.consolidate_select({
        "plan_pmg": listado_inicial,
        "interv_abogado": A,
        "interv_implementador": I,
        "interv_desarrollador": D,
        "dimension": DIM_FILTER,
        "subdimension": datos_pregunta["subdimension"],
    }) or {}
    
    plan_text = _as_text(
        (cons.get("payload") or {}).get("plan_intercalado", "")
        or (cons.get("payload") or {}).get("plan_pmg", "")
        or "\n".join((cons.get("payload") or {}).get("listado", []))
    )
    
    # Tomar primera línea y limpiar numeración
    first_line = plan_text.strip().splitlines()[0] if plan_text.strip() else listado_inicial
    m = NUM_PAT.match(first_line)
    actividad = (m.group(2) if m else first_line).strip(" .;-")
    return actividad

def generar_hito_para_indicador_comite(indicador, datos_pregunta, pmg, abo_srv, imp_srv, dev_srv):
    """
    Genera UN hito específico para un indicador usando el Comité.
    Replica la lógica de generar_hito_con_comite del bulk processor.
    """
    contexto = (
        f"Definir un HITO concreto y verificable para el indicador '{indicador}' "
        f"en la subdimensión {datos_pregunta['subdimension']} usando el instrumento "
        f"{datos_pregunta['instrumento']}."
    )
    
    listado = (
        f"Indicador: {indicador}. Brecha: {datos_pregunta['brecha']}. "
        "Generar UN solo hito como entregable final, sin porcentajes, que represente el cumplimiento del indicador."
    )
    
    prop = pmg.propose_hito({
        "dimension": DIM_FILTER,
        "subdimension": datos_pregunta["subdimension"],
        "brecha": datos_pregunta["brecha"],
        "pregunta": listado,
        "listado": listado,
    }) or {}
    
    raw_h = []
    if prop.get("status") == "error" and "Invalid JSON" in prop.get("message", ""):
        print("  ⚠️  Error JSON en propose_hito (hito indicador). Intentando limpiar...")
        raw = prop.get("raw", "")
        import json
        
        cleaned = re.sub(r'^```(?:json)?\s*', "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```\s*$', "", cleaned, flags=re.MULTILINE)
        try:
            data = json.loads(cleaned.strip())
            raw_h = data if isinstance(data, list) else data.get("hitos", [])
        except Exception as e2:
            print(f"  ❌ Error parseando JSON limpio en hito indicador: {e2}")
            raw_h = []
    else:
        raw_h = (prop.get("payload") or {}).get("hitos") or []
    
    hitos_texto = []
    for h in raw_h:
        if isinstance(h, dict):
            hitos_texto.append(h.get("texto", ""))
        else:
            hitos_texto.append(str(h))
    
    if not hitos_texto:
        hitos_texto = [
            f"HITO 1: Indicador '{indicador}' implementado y verificado en el sitio institucional",
        ]
    
    payload_inter = {
        "contexto_pm": contexto,
        "listado_vigente": "\n".join(hitos_texto),
    }
    
    A = _as_text((abo_srv.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    I = _as_text((imp_srv.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    D = _as_text((dev_srv.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    
    cons = pmg.consolidate_select({
        "plan_pmg": "\n".join(hitos_texto),
        "interv_abogado": A,
        "interv_implementador": I,
        "interv_desarrollador": D,
        "dimension": DIM_FILTER,
        "subdimension": datos_pregunta["subdimension"],
    }) or {}
    
    plan_text = _as_text(
        (cons.get("payload") or {}).get("plan_intercalado", "")
        or (cons.get("payload") or {}).get("plan_pmg", "")
        or "\n".join((cons.get("payload") or {}).get("listado", []))
    )
    
    first_line = plan_text.strip().splitlines()[0] if plan_text.strip() else hitos_texto[0]
    first_line = RE_HITO.sub("", first_line).strip(": -")
    return first_line

def generar_indicador_resultado_subdimension_comite(subdimension, dimension, pmg):
    """
    Genera un indicador cualitativo de resultado para UNA SUBDIMENSIÓN completa
    usando el PMG del Comité. Usa generate_result_indicator con fallback.
    """
    try:
        result = pmg.generate_result_indicator({
            "dimension": dimension,
            "subdimension": subdimension,
            "instrumento": "",
            "plan_text": f"Indicador cualitativo de resultado para la subdimensión {subdimension} de {dimension}"
        })
        indicador = (result.get("payload") or {}).get("indicador", "")
        if indicador and indicador.strip():
            # Limpiar formato
            indicador = indicador.strip('"').strip("'")
            if indicador.endswith('.'):
                indicador = indicador[:-1]
            # Tomar solo primera línea
            if '\n' in indicador:
                indicador = indicador.split('\n')[0].strip()
            return indicador
    except Exception as e:
        print(f"  ⚠️  Error generando indicador de resultado: {e}")
    
    # Fallback
    return f"Calidad web institucional consolidada para la subdimensión {subdimension}"

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main(nombre_subdimension, instrumento):
    """Función principal que ejecuta el flujo completo para UNA subdimensión + instrumento"""
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLAN PTD - SUBDIMENSIÓN + INSTRUMENTO ESPECÍFICOS (COMITÉ)")
    print("   Calidad Web y Servicios Digitales → PostgreSQL")
    print("="*80)
    print(f"📌 Subdimensión: {nombre_subdimension}")
    print(f"📌 Instrumento: {instrumento}")
    print(f"🔍 ID de grupo de procesos: {GRUPO_PROCESOS}")
    print("="*80 + "\n")
    
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
                WHERE Dimension = %s
                  AND N_Pregunta IS NOT NULL
                ORDER BY Subdimension, Instrumento
            """, (DIM_FILTER,))
            for subdim, inst in cursor.fetchall():
                print(f"   • {subdim}")
                print(f"     → {inst}")
            cursor.close()
            conn.close()
            return
        
        # Inicializar servidores MCP
        print("🔧 Inicializando servidores MCP...")
        pmg = pmg_srv.PMGServer(grupo_procesos=GRUPO_PROCESOS)
        print("✅ Servidores MCP inicializados\n")
        
        # Paso 2: Generar indicador de resultado para la subdimensión
        print("🔄 Generando indicador de resultado para subdimensión...")
        dimension = preguntas[0]['dimension']
        indicador_resultado = generar_indicador_resultado_subdimension_comite(
            nombre_subdimension, dimension, pmg
        )
        print(f"✅ Indicador de resultado: {indicador_resultado}\n")
        
        # Paso 3: Generar actividades e hitos con Comité
        print("🔄 Generando actividades e hitos con debate del Comité...\n")
        
        indicador_anterior = None
        actividades_generadas = []
        hitos_generados = {}
        
        for idx, pregunta in enumerate(preguntas, 1):
            indicador_actual = pregunta['indicador']
            
            # Si es nuevo indicador, generar hito primero
            if indicador_actual not in hitos_generados:
                print(f"   Generando hito para indicador '{indicador_actual}'...")
                hito = generar_hito_para_indicador_comite(
                    indicador_actual, pregunta, pmg, abo_srv, imp_srv, dev_srv
                )
                hitos_generados[indicador_actual] = hito
                print(f"   ✅ Hito generado: {hito[:60]}...")
            
            # Generar actividad usando el hito del indicador
            print(f"   [{idx}/{len(preguntas)}] Generando actividad para pregunta #{pregunta['n_pregunta']}...")
            actividad = generar_actividad_para_pregunta_comite(
                pregunta,
                hitos_generados[indicador_actual],
                pmg,
                abo_srv,
                imp_srv,
                dev_srv
            )
            actividades_generadas.append({
                'pregunta_data': pregunta,
                'actividad': actividad,
                'indicador': indicador_actual
            })
            print(f"       → Actividad: {actividad[:80]}...")
        
        print(f"\n✅ Total actividades generadas: {len(actividades_generadas)}")
        print(f"✅ Total hitos únicos generados: {len(hitos_generados)}\n")
        
        # Paso 4: Eliminar plan antiguo
        print("🗑️  Verificando y eliminando plan antiguo...")
        registros_eliminados = eliminar_plan_antiguo(
            conn,
            dimension,
            nombre_subdimension,
            instrumento,
            AUTOR
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
              AND Autor = %s
            GROUP BY Tipo
            ORDER BY total DESC
        """, (dimension, nombre_subdimension, instrumento, AUTOR))
        
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
