#!/usr/bin/env python3
"""
Script Refactorizado: Generación de Planes PTD con Comité - Calidad Web
Arquitectura: Multi-agente (Comité) → Generación por subdimensión+instrumento → Estructura normalizada
Fecha: 2025-11-10

FLUJO:
1. Sin argumentos - procesa TODAS las combinaciones (subdimensión + instrumento)
2. Por cada combinación:
   - Comité debate y genera plan
   - Se parsea en actividades/hitos individuales
   - Se elimina plan antiguo (autor='Comite')
   - Se insertan nuevas filas
3. Repite para siguiente combinación

IDENTIFICACIÓN ÚNICA:
- Calidad Web: dimension + subdimension + instrumento
- Instrumentos: Medición DGDU, Evaluación heurística, Focus groups, etc.
"""
from __future__ import annotations
import sys, os, re
from typing import Dict, Any, List, Tuple
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
    from mcp.servers import mcp_server_secretario as sec_srv
    
    return pmg_srv, abo_srv, imp_srv, dev_srv, sec_srv

pmg_srv, abo_srv, imp_srv, dev_srv, sec_srv = _import_servers()

RE_HITO = re.compile(r"^\s*HITO\s*\d*\s*:\s*", flags=re.IGNORECASE)
NUM_PAT = re.compile(r"^\s*(\d+)\s*[\.\-)]\s*(.*)$", re.UNICODE)

def conectar_db():
    """Establece conexión con PostgreSQL usando psycopg2"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        raise

def leer_preguntas_desde_db(conn) -> List[Dict[str, Any]]:
    """Lee todas las PREGUNTAS de Calidad Web desde PostgreSQL.

    Esta función replica la lógica de `agente maestro/main_calidad_web.py` pero
    se usará en el flujo con Comité. No lee combinaciones sino cada fila de
    pregunta, que luego agruparemos por (Subdimension, Instrumento).
    """
    print("\n" + "=" * 80)
    print("📂 LEYENDO PREGUNTAS DESDE POSTGRESQL")
    print("=" * 80 + "\n")

    cursor = conn.cursor()

    sql = f"""
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
    FROM {TABLE}
    WHERE Dimension = %s
      AND N_Pregunta IS NOT NULL
    ORDER BY Subdimension, Indicador, N_Pregunta
    """

    try:
        cursor.execute(sql, (DIM_FILTER,))
        filas = cursor.fetchall()

        preguntas: List[Dict[str, Any]] = []
        for fila in filas:
            preguntas.append({
                "dimension": fila[0],
                "subdimension": fila[1],
                "instrumento": fila[2],
                "indicador": fila[3],
                "brecha": fila[4],
                "n_pregunta": fila[5],
                "pregunta": fila[6],
                "iniciativa": fila[7],
                "objetivo_iniciativa": fila[8],
                "indicador_proceso": fila[9],
            })

        cursor.close()

        print(f"📊 Total preguntas leídas: {len(preguntas)}")

        subdimensiones_unicas: Dict[str, int] = {}
        for p in preguntas:
            key = p["subdimension"]
            subdimensiones_unicas[key] = subdimensiones_unicas.get(key, 0) + 1

        print("\n📋 Preguntas por subdimensión:")
        for subdim, count in subdimensiones_unicas.items():
            print(f"   • {subdim}: {count} preguntas")
        print()

        return preguntas

    except Exception as e:
        print(f"❌ Error leyendo preguntas: {e}")
        cursor.close()
        raise

def eliminar_plan_antiguo(conn, dimension, subdimension, instrumento, autor):
    """
    Elimina los registros antiguos de un plan específico de Calidad Web
    
    Args:
        conn: Conexión a PostgreSQL
        dimension: Dimensión del plan
        subdimension: Subdimensión del plan
        instrumento: Instrumento del plan
        autor: Autor del plan ('Comite')
        
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

def parsear_plan_a_registros(plan_texto):
    """
    Parsea el plan generado por el Comité y extrae actividades e hitos
    
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
        
        # Detectar HITO
        if _is_hito(linea):
            # Extraer descripción del hito
            hito_texto = RE_HITO.sub("", linea).strip(": -")
            if hito_texto:
                elementos.append((numero, 'Hito', hito_texto))
                numero += 1
        else:
            # Es una actividad - remover numeración si existe
            m = NUM_PAT.match(linea)
            actividad_texto = (m.group(2) if m else linea).strip(" .;-")
            if actividad_texto:
                elementos.append((numero, 'Actividad', actividad_texto))
                numero += 1
    
    return elementos

def _as_text(x) -> str:
    if x is None: return ""
    if isinstance(x, list): return "\n".join(str(i).strip() for i in x if str(i).strip())
    return str(x)

def _is_hito(s: str) -> bool:
    return bool(re.match(r"^\s*HITO\s+\d+\s*:\s*", s or "", flags=re.IGNORECASE))

def _normalize_numbered(lines: List[str]) -> List[str]:
    out, n = [], 1
    for ln in lines:
        if _is_hito(ln):
            out.append(ln)
        else:
            m = NUM_PAT.match(ln)
            body = (m.group(2) if m else ln).strip(" .;-")
            out.append(f"{n}.- {body}")
            n += 1
    return out

def enforce_hito_count(hitos: List[str]) -> List[str]:
    target = 4
    fixed=[]; n=1
    for h in hitos:
        s = RE_HITO.sub("", str(h)).strip(": -")
        if s:
            fixed.append(f"HITO {n}: {s}"); n+=1
    stages = [
        "Configuración técnica completada en ambiente de pruebas",
        "Pruebas/certificación superadas",
        "En producción con seguimiento básico",
        "Brecha cerrada y verificación documentada",
    ]
    while len(fixed) < target:
        idx = len(fixed)
        fixed.append(f"HITO {idx+1}: {stages[idx]}")
    if len(fixed) > target:
        fixed = fixed[:target]
    out=[]; n=1
    for h in fixed:
        s = RE_HITO.sub("", h).strip(": -")
        out.append(f"HITO {n}: {s}"); n+=1
    return out

# ==================== PATRONES Y FUNCIONES AUXILIARES ====================
NUM_PAT = re.compile(r'^(\d+)[.\-\)]?\s+(.+)')
RE_HITO = re.compile(r'^\**\s*(?:HITO|Hito|hito)\s+(\d+)\s*:?\s*\**', re.IGNORECASE)

def _is_hito(line: str) -> bool:
    """Verifica si una línea representa un hito"""
    if not line:
        return False
    line = line.strip()
    return bool(RE_HITO.match(line))

def enforce_hito_count(hitos: list, n_required: int = 4) -> list:
    """
    Asegura que existan exactamente n_required hitos
    Si hay menos, duplica el último
    Si hay más, toma los primeros n_required
    """
    nh = len(hitos)
    if nh == n_required:
        return hitos
    elif nh < n_required:
        print(f"  ⚠️  Solo hay {nh} hitos. Se duplicará el último para completar {n_required}.")
        return hitos + [hitos[-1]]*(n_required - nh) if hitos else []
    else:
        print(f"  ⚠️  Hay {nh} hitos. Se tomarán solo los primeros {n_required}.")
        return hitos[:n_required]

def ensure_acciones_alineadas_a_hitos(plan_text: str, hitos_texto: str) -> str:
    """Asegura que el plan tenga hitos alineados con las acciones"""
    if isinstance(plan_text, list):
        plan_text = "\n".join(str(x).strip() for x in plan_text if str(x).strip())
    
    lines = [ln.strip() for ln in str(plan_text or "").splitlines() if ln.strip()]
    if not lines:
        return ""
    
    # Si ya tiene hitos, retornar
    if any(_is_hito(ln) for ln in lines):
        return "\n".join(lines)
    
    # Si no tiene hitos, retornar tal cual (los hitos se generan en la fase de debate)
    return "\n".join(lines)

# ==================== PROCESAMIENTO DE COMBINACIONES ====================

def generar_indicador_resultado_subdimension(subdimension: str, dimension: str, pmg) -> str:
    """Genera un indicador de resultado CUALITATIVO para una subdimensión.

    Para mantener coherencia con el resto de dimensiones, delegamos la
    generación al servidor PMG, pero con un prompt orientado a resultado
    cualitativo. Si falla, usamos un fallback genérico.
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
            return indicador.strip()
    except Exception as e:
        print(f"  ⚠️  Error generando indicador de resultado para subdimensión: {e}")

    return f"Calidad web institucional consolidada para la subdimensión {subdimension}"


def generar_actividad_con_comite(pregunta: Dict[str, Any], hito_indicador: str, pmg, abo, imp, dev) -> str:
    """Genera UNA actividad concreta para una pregunta usando el Comité.

    Equivalente conceptual a `generar_actividad_para_pregunta` del Agente
    Maestro, pero usando PMG + intervenciones de los agentes especializados.
    """
    contexto = (
        f"Dimensión: {pregunta['dimension']}. Subdimensión: {pregunta['subdimension']}. "
        f"Instrumento: {pregunta['instrumento']}. Indicador: {pregunta['indicador']}. "
        f"Brecha: {pregunta['brecha']}. Iniciativa: {pregunta['iniciativa']}. "
        f"Objetivo: {pregunta['objetivo_iniciativa']}. Indicador de proceso: {pregunta['indicador_proceso']}.")

    base_listado = (
        f"Pregunta #{pregunta['n_pregunta']}: {pregunta['pregunta']}. "
        "Generar UNA actividad concreta y medible que permita pasar de NO cumple a SÍ cumple."
    )

    # PMG propone actividad inicial usando el hito del indicador como "hitos_previos"
    prop = pmg.generate_initial({
        "dimension": DIM_FILTER,
        "subdimension": pregunta["subdimension"],
        "brecha": pregunta["brecha"],
        "pregunta": pregunta["pregunta"],
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

    A = _as_text((abo.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    I = _as_text((imp.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    D = _as_text((dev.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))

    cons = pmg.consolidate_select({
        "plan_pmg": listado_inicial,
        "interv_abogado": A,
        "interv_implementador": I,
        "interv_desarrollador": D,
        "dimension": DIM_FILTER,
        "subdimension": pregunta["subdimension"],
    }) or {}

    plan_text = _as_text(
        (cons.get("payload") or {}).get("plan_intercalado", "")
        or (cons.get("payload") or {}).get("plan_pmg", "")
        or "\n".join((cons.get("payload") or {}).get("listado", []))
    )

    # Tomar solo la primera línea como actividad principal
    first_line = plan_text.strip().splitlines()[0] if plan_text.strip() else listado_inicial
    m = NUM_PAT.match(first_line)
    actividad = (m.group(2) if m else first_line).strip(" .;-")
    return actividad


def generar_hito_con_comite(indicador: str, ejemplo_pregunta: Dict[str, Any], pmg, abo, imp, dev) -> str:
    """Genera UN hito específico para un indicador usando el Comité."""
    contexto = (
        f"Definir un HITO concreto y verificable para el indicador '{indicador}' "
        f"en la subdimensión {ejemplo_pregunta['subdimension']} usando el instrumento "
        f"{ejemplo_pregunta['instrumento']}."
    )

    listado = (
        f"Indicador: {indicador}. Brecha: {ejemplo_pregunta['brecha']}. "
        "Generar UN solo hito como entregable final, sin porcentajes, que represente el cumplimiento del indicador."
    )

    prop = pmg.propose_hito({
        "dimension": DIM_FILTER,
        "subdimension": ejemplo_pregunta["subdimension"],
        "brecha": ejemplo_pregunta["brecha"],
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

    hitos_texto: List[str] = []
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

    A = _as_text((abo.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    I = _as_text((imp.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))
    D = _as_text((dev.intervention(payload_inter).get("payload", {}) or {}).get("intervencion", ""))

    cons = pmg.consolidate_select({
        "plan_pmg": "\n".join(hitos_texto),
        "interv_abogado": A,
        "interv_implementador": I,
        "interv_desarrollador": D,
        "dimension": DIM_FILTER,
        "subdimension": ejemplo_pregunta["subdimension"],
    }) or {}

    plan_text = _as_text(
        (cons.get("payload") or {}).get("plan_intercalado", "")
        or (cons.get("payload") or {}).get("plan_pmg", "")
        or "\n".join((cons.get("payload") or {}).get("listado", []))
    )

    first_line = plan_text.strip().splitlines()[0] if plan_text.strip() else hitos_texto[0]
    first_line = RE_HITO.sub("", first_line).strip(": -")
    return first_line


def procesar_grupo(
    conn,
    subdimension: str,
    instrumento: str,
    preguntas_grupo: List[Dict[str, Any]],
    pmg,
    abo,
    imp,
    dev,
) -> int:
    """Procesa un grupo (subdimensión + instrumento) al estilo del Agente Maestro.

    - Genera indicador de resultado a nivel de subdimensión
    - Genera 1 actividad por pregunta
    - Genera 1 hito por indicador
    - Inserta hitos cuando cambia de indicador y al final del último
    """

    print("\n" + "=" * 80)
    print(f"📋 PROCESANDO GRUPO: {subdimension} / {instrumento}")
    print(f"   Total preguntas: {len(preguntas_grupo)}")
    print("=" * 80)

    if not preguntas_grupo:
        print("  ⚠️  Grupo sin preguntas, se omite.")
        return 0

    dimension = preguntas_grupo[0]["dimension"]

    print("\n🎯 Generando indicador de resultado de subdimensión con PMG...")
    indicador_resultado = generar_indicador_resultado_subdimension(subdimension, dimension, pmg)
    print(f"  ✅ Indicador de resultado: {indicador_resultado[:120]}\n")

    indicador_anterior: str | None = None
    actividades_generadas: List[Dict[str, Any]] = []
    hitos_generados: Dict[str, str] = {}

    print("🔄 Generando actividades e hitos por indicador/pregunta (Comité)...\n")

    for pregunta in preguntas_grupo:
        indicador_actual = pregunta["indicador"]

        # Si es la primera vez que vemos este indicador, generamos su hito
        if indicador_actual not in hitos_generados:
            hito = generar_hito_con_comite(indicador_actual, pregunta, pmg, abo, imp, dev)
            hitos_generados[indicador_actual] = hito
            print(f"   ✅ Hito generado para indicador '{indicador_actual}': {hito[:60]}...")

        actividad = generar_actividad_con_comite(
            pregunta,
            hitos_generados[indicador_actual],
            pmg,
            abo,
            imp,
            dev,
        )

        actividades_generadas.append({
            "pregunta_data": pregunta,
            "actividad": actividad,
            "indicador": indicador_actual,
        })

    print(f"\n✅ Total actividades generadas: {len(actividades_generadas)}")
    print(f"✅ Total hitos únicos generados: {len(hitos_generados)}\n")

    print("🗑️  Eliminando plan antiguo (autor=Comite)...")
    eliminados = eliminar_plan_antiguo(conn, dimension, subdimension, instrumento, AUTOR)
    if eliminados:
        print(f"  → {eliminados} registros antiguos eliminados")
    else:
        print("  → No había plan antiguo del Comité para este grupo")

    print("\n💾 Insertando nuevo plan (Comité, lógica Calidad Web)...")

    indicador_anterior = None
    hito_pendiente: str | None = None
    datos_hito_pendiente: Dict[str, Any] | None = None
    n_secuencial = 0
    registros_insertados = 0

    for item in actividades_generadas:
        pregunta_data = item["pregunta_data"]
        actividad = item["actividad"]
        indicador_actual = item["indicador"]

        datos_fila = {
            "dimension": pregunta_data["dimension"],
            "subdimension": pregunta_data["subdimension"],
            "instrumento": pregunta_data["instrumento"],
            "indicador": pregunta_data["indicador"],
            "brecha": pregunta_data["brecha"],
            "n_pregunta": pregunta_data["n_pregunta"],
            "pregunta": pregunta_data["pregunta"],
            "iniciativa": pregunta_data["iniciativa"],
            "objetivo_iniciativa": pregunta_data["objetivo_iniciativa"],
            "indicador_proceso": pregunta_data["indicador_proceso"],
            "indicador_resultado": indicador_resultado,
        }

        if indicador_actual != indicador_anterior and hito_pendiente and datos_hito_pendiente:
            n_secuencial += 1
            insertar_registro(conn, datos_hito_pendiente, n_secuencial, "Hito", hito_pendiente)
            registros_insertados += 1

        n_secuencial += 1
        insertar_registro(conn, datos_fila, n_secuencial, "Actividad", actividad)
        registros_insertados += 1

        hito_pendiente = hitos_generados[indicador_actual]
        datos_hito_pendiente = datos_fila.copy()
        indicador_anterior = indicador_actual

    if hito_pendiente and datos_hito_pendiente:
        n_secuencial += 1
        insertar_registro(conn, datos_hito_pendiente, n_secuencial, "Hito", hito_pendiente)
        registros_insertados += 1

    conn.commit()

    print(f"  ✅ Grupo completado: {registros_insertados} registros insertados\n")
    return registros_insertados


def main():
    """Flujo principal para Calidad Web con Comité (pregunta/indicador).

    1. Lee todas las preguntas de la dimensión de Calidad Web
    2. Agrupa por (Subdimensión, Instrumento)
    3. Para cada grupo aplica la misma lógica que `main_calidad_web.py`,
       pero usando el Comité en vez del Agente Maestro.
    """

    print("\n" + "=" * 80)
    print("🚀 INICIO: Generación de Planes PTD - Calidad Web (Comité)")
    print("=" * 80)

    try:
        conn = conectar_db()
        conn.autocommit = False
        print("✅ Conexión establecida con PostgreSQL\n")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

    try:
        preguntas = leer_preguntas_desde_db(conn)
    except Exception as e:
        print(f"❌ Error leyendo preguntas: {e}")
        conn.close()
        sys.exit(1)

    if not preguntas:
        print("⚠️  No se encontraron preguntas para procesar.")
        conn.close()
        return

    print("= " * 40)
    print("📊 AGRUPANDO PREGUNTAS POR SUBDIMENSIÓN + INSTRUMENTO")
    print("= " * 40 + "\n")

    grupos: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for p in preguntas:
        key = (p["subdimension"], p["instrumento"])
        grupos.setdefault(key, []).append(p)

    print(f"✅ Total grupos (planes únicos): {len(grupos)}\n")

    print("🔧 Inicializando servidores MCP...")
    pmg = pmg_srv.PMGServer()
    print("✅ Servidor PMG inicializado\n")

    total_grupos = len(grupos)
    grupos_procesados = 0
    total_registros = 0
    fallidos = 0

    for idx, ((subdimension, instrumento), preguntas_grupo) in enumerate(grupos.items(), 1):
        print("\n" + "=" * 80)
        print(f"📦 Grupo {idx}/{total_grupos}: {subdimension} - {instrumento}")
        print("=" * 80)
        try:
            registros = procesar_grupo(
                conn,
                subdimension,
                instrumento,
                preguntas_grupo,
                pmg,
                abo_srv,
                imp_srv,
                dev_srv,
            )
            total_registros += registros
            grupos_procesados += 1
        except Exception as e:
            fallidos += 1
            print(f"❌ Error en grupo {idx} ({subdimension} - {instrumento}): {e}")
            conn.rollback()

    conn.close()

    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL")
    print("=" * 80)
    print(f"✅ Grupos procesados: {grupos_procesados}/{total_grupos}")
    print(f"❌ Grupos fallidos: {fallidos}")
    print(f"📝 Total registros insertados: {total_registros}")
    prom = total_registros / grupos_procesados if grupos_procesados else 0
    print(f"📊 Promedio registros/grupo: {prom:.1f}")
    print("=" * 80 + "\n")

    print("🔌 Conexión cerrada")
    print("✨ Proceso completado\n")


if __name__ == "__main__":
    main()
