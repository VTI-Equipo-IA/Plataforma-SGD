#!/usr/bin/env python3
"""
Subscript Comité: Generación de Plan PTD para UNA Subdimensión - Gobernanza de Datos
Procesa una subdimensión + nivel específicos desde PostgreSQL → Comité debate → Actualiza PostgreSQL
Fecha: 2025-11-10 (Refactorizado 2025-11-20)

USO:
    python generar_plan_subdimension_gd.py "<nombre_subdimension>" "<nivel_madurez>"
    
    Ejemplo:
    python generar_plan_subdimension_gd.py "Organización" "Basico"
    python generar_plan_subdimension_gd.py "Arquitectura" "Medio"

FLUJO (equivalente a script masivo, centrado en 1 combinación):
1. Recibe subdimensión y nivel de madurez como argumentos
2. Lee datos (incluye Indicador_Resultado previo) desde PostgreSQL
3. Comité debate y genera hitos (enforce: exactamente 4, con fallback descriptivo)
4. Comité debate plan (hasta 3 rondas, votación unánime anticipa fin)
5. Genera Indicador de Resultado (FASE 2.5) si falta, usando servidor PMG
6. Normaliza plan: numeración de actividades, preserva hitos, recorta líneas posteriores al último hito
7. Parsea a registros (actividades / hitos)
8. Elimina plan anterior Autor='Comite'
9. Inserta nuevos registros asegurando Indicador_Resultado no nulo
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
DIM_FILTER = "Gobernanza de datos"
AUTOR = "Comite"

# Generar ID único para esta ejecución
GRUPO_PROCESOS = f"comite_gd_{uuid.uuid4().hex[:12]}"

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

NUM_PAT = re.compile(r'^\s*(\d+)[.\-\)]?\s*(.+)$', re.UNICODE)
RE_HITO = re.compile(r"^\s*HITO\s*\d*\s*:\s*", flags=re.IGNORECASE)

def _is_hito(line: str) -> bool:
    return bool(re.match(r"^\s*HITO\s+\d+\s*:\s*", line or "", flags=re.IGNORECASE))

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

def _as_text(x) -> str:
    if x is None: return ""
    if isinstance(x, list): return "\n".join(str(i).strip() for i in x if str(i).strip())
    return str(x)

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

def ensure_acciones_alineadas_a_hitos(plan_text: str, datos_comb: dict, pmg) -> str:
    if isinstance(plan_text, list):
        plan_text = "\n".join(str(x).strip() for x in plan_text if str(x).strip())
    lines = [ln.strip() for ln in str(plan_text or "").splitlines() if ln.strip()]
    if not lines:
        return ""
    if any(_is_hito(ln) for ln in lines):
        out = _normalize_numbered(lines)
        last = max((i for i,ln in enumerate(out) if _is_hito(ln)), default=None)
        if last is not None and last < len(out)-1:
            out = out[:last+1]
        return "\n".join(out)
    resp = pmg.propose_hito({
        "dimension": DIM_FILTER,
        "subdimension": datos_comb['subdimension'],
        "nivel_madurez": datos_comb['nivel_madurez'],
        "brecha": datos_comb.get('brecha', ''),
        "pregunta": f"¿Cómo avanzar desde nivel {datos_comb['nivel_madurez']} hacia el siguiente nivel?",
        "listado": "\n".join(lines),
    })
    raw = (resp.get("payload") or {}).get("hitos") or []
    hitos = []
    for h in raw:
        if isinstance(h, dict): hitos.append(h.get("texto",""))
        else: hitos.append(str(h))
    hitos = enforce_hito_count(hitos)
    out = _normalize_numbered(lines)
    if not out or not _is_hito(out[-1]):
        out.append(hitos[-1] if hitos else "HITO 1: Resultado alcanzado")
    return "\n".join(out)

def generar_indicador_resultado(plan_text: str, datos_comb: dict, pmg) -> str:
    try:
        resp = pmg.generate_result_indicator({
            "dimension": DIM_FILTER,
            "subdimension": datos_comb['subdimension'],
            "nivel_madurez": datos_comb['nivel_madurez'],
            "brecha": datos_comb.get('brecha', ''),
            "pregunta": "",
            "respuesta": datos_comb.get('respuesta', 'No'),
            "plan_pmg": plan_text,
            "contexto_pm": "",
            "indicador_prev": datos_comb.get('indicador_resultado','') or "",
            "interv_abogado": "",
            "interv_implementador": "",
            "interv_desarrollador": ""
        })
        indicador = (resp.get("payload") or {}).get("indicador_resultado", "")
        if indicador and indicador.strip():
            return indicador.strip()
    except Exception as e:
        print(f"  ⚠️ Error generando indicador de resultado: {e}")
    contexto = f"{datos_comb['subdimension']} - Nivel {datos_comb['nivel_madurez']}"
    return f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"

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

def leer_datos_combinacion(conn, nombre_subdimension, nivel_madurez):
    """
    Lee los datos de UNA combinación (subdimensión + nivel) desde PostgreSQL
    
    Returns:
        Dict con los datos o None si no existe
    """
    print("\n" + "="*80)
    print(f"📂 LEYENDO DATOS: {nombre_subdimension} - Nivel: {nivel_madurez}")
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
        Indicador_Proceso,
        Indicador_Resultado
    FROM ptd_planes
    WHERE Dimension = %s
      AND Subdimension = %s
      AND Nivel_de_madurez = %s
    LIMIT 1
    """
    
    try:
        cursor.execute(sql, (DIM_FILTER, nombre_subdimension, nivel_madurez))
        fila = cursor.fetchone()
        
        if not fila:
            print(f"❌ No se encontraron datos para '{nombre_subdimension}' con nivel '{nivel_madurez}'")
            cursor.close()
            return None
        
        datos_comb = {
            'dimension': fila[0],
            'subdimension': fila[1],
            'instrumento': fila[2],
            'indicador': fila[3],
            'brecha': fila[4],
            'nivel_madurez': fila[5],
            'iniciativa': fila[6],
            'objetivo_iniciativa': fila[7],
            'indicador_proceso': fila[8],
            'indicador_resultado': fila[9] or ""
        }
        
        cursor.close()
        
        print(f"✅ Datos leídos exitosamente:")
        print(f"   → Dimensión: {datos_comb['dimension']}")
        print(f"   → Subdimensión: {datos_comb['subdimension']}")
        print(f"   → Nivel: {datos_comb['nivel_madurez']}")
        print(f"   → Brecha: {datos_comb['brecha'][:100]}...")
        prev_ind = datos_comb.get('indicador_resultado')
        if prev_ind:
            print(f"   → Indicador Resultado previo (preview): {prev_ind[:80]}{'...' if len(prev_ind)>80 else ''}")
        print()
        
        return datos_comb
        
    except Exception as e:
        print(f"❌ Error leyendo combinación: {e}")
        cursor.close()
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
    
    # Asegurar que indicador_resultado NUNCA sea NULL
    indicador_resultado = datos_fila.get('indicador_resultado')
    if not indicador_resultado or not str(indicador_resultado).strip():
        contexto = f"{datos_fila['subdimension']} - Nivel {datos_fila['nivel_madurez']}"
        indicador_resultado = f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"
    
    valores = (
        datos_fila['dimension'],
        datos_fila['subdimension'],
        datos_fila['instrumento'],
        datos_fila['indicador'],
        datos_fila['brecha'],
        datos_fila['nivel_madurez'],  # Gobernanza SÍ tiene nivel
        None,  # N_Pregunta (NULL)
        None,  # Pregunta (NULL - Gobernanza no tiene pregunta)
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
    """Parsea el plan generado por el Comité y extrae actividades e hitos"""
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

# ============================================================================
# FUNCIÓN DE PROCESAMIENTO
# ============================================================================

def procesar_combinacion(conn, datos_comb, pmg, abo_srv, imp_srv, dev_srv):
    """
    Procesa una combinación (subdimensión + nivel) y genera plan con el Comité
    
    FASE 1: Debate de HITOS (4 obligatorios)
    FASE 2: Debate de PLAN (3 rondas máximo)
    FASE 3: Parsear plan en actividades/hitos
    FASE 4: Eliminar plan antiguo + Insertar nuevos registros
    
    Returns:
        Número de registros insertados
    """
    sub = datos_comb['subdimension']
    nivel = datos_comb['nivel_madurez']
    
    print("\n" + "="*80)
    print(f"🔹 PROCESANDO: {sub} - Nivel: {nivel}")
    print("="*80)
    
    # ========== FASE 1: DEBATE DE HITOS ==========
    print("\n📍 FASE 1: Debate de HITOS")
    print("-" * 80)
    
    # Incluir brecha y pregunta contextual para que PMG tenga suficiente información
    prop = pmg.propose_hito({
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "nivel_madurez": nivel,
        "brecha": datos_comb.get('brecha', ''),
        "pregunta": f"¿Cómo avanzar desde nivel {nivel} hacia el siguiente nivel?",
        "listado": "",
    })
    raw_h = (prop.get("payload") or {}).get("hitos") or []
    hitos = []
    for h in raw_h:
        if isinstance(h, dict): 
            hitos.append(h.get("texto",""))
        else: 
            hitos.append(str(h))
    
    payload_h = {
        "contexto_pm": f"Definir 4 HITOS claros y medibles para la subdimensión {sub} nivel {nivel}.",
        "listado_vigente": "\\n".join(hitos)
    }
    
    print("  → PMG propone hitos iniciales")
    print("  → Abogado revisa aspectos legales...")
    A = _as_text((abo_srv.intervention(payload_h).get("payload",{}) or {}).get("intervencion",""))
    
    print("  → Implementador revisa factibilidad...")
    I = _as_text((imp_srv.intervention(payload_h).get("payload",{}) or {}).get("intervencion",""))
    
    print("  → Desarrollador revisa aspectos técnicos...")
    D = _as_text((dev_srv.intervention(payload_h).get("payload",{}) or {}).get("intervencion",""))
    
    print("  → PMG consolida intervenciones...")
    pmg.consolidate_select({
        "plan_pmg": "\\n".join(hitos),
        "interv_abogado": A,
        "interv_implementador": I,
        "interv_desarrollador": D,
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "nivel_madurez": nivel
    })
    
    final_hitos = enforce_hito_count(hitos)
    print(f"  ✅ {len(final_hitos)} hitos definidos\n")
    
    # ========== FASE 2: DEBATE DE PLAN ==========
    print("\n📝 FASE 2: Debate de PLAN")
    print("-" * 80)
    
    contexto = (
        f"Plan PTD de gobernanza para avanzar desde nivel {nivel}. "
        "Debe tener 4 HITOS obligatorios y 3–4 acciones por cada uno."
    )
    
    print("  → PMG genera plan inicial...")
    init = pmg.generate_initial({
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "nivel_madurez": nivel,
        "hitos_previos": "\\n".join(final_hitos),
        "brecha": datos_comb.get('brecha', ''),
        "pregunta": "",
        "respuesta": datos_comb.get('respuesta', 'No'),
        "listado": "",
        "contexto_pm": contexto
    }).get("payload",{})
    
    plan_text = _as_text(init.get("plan_intercalado","") or init.get("plan_pmg","") or init.get("listado",""))
    
    print(f"  → PMG generó plan inicial ({len(plan_text)} chars)")
    
    # Rondas de debate
    for ronda in range(1, 4):
        print(f"\n  🔄 Ronda {ronda} de debate:")
        
        inter_payload = {"contexto_pm": contexto, "listado_vigente": plan_text}
        
        print(f"    → Abogado interviene...")
        Ai = _as_text((abo_srv.intervention(inter_payload).get("payload",{}) or {}).get("intervencion",""))
        
        print(f"    → Implementador interviene...")
        Ii = _as_text((imp_srv.intervention(inter_payload).get("payload",{}) or {}).get("intervencion",""))
        
        print(f"    → Desarrollador interviene...")
        Di = _as_text((dev_srv.intervention(inter_payload).get("payload",{}) or {}).get("intervencion",""))
        
        print(f"    → PMG consolida...")
        cons = pmg.consolidate_select({
            "hitos_previos": "\\n".join(final_hitos),
            "plan_pmg": plan_text,
            "interv_abogado": Ai,
            "interv_implementador": Ii,
            "interv_desarrollador": Di,
            "dimension": DIM_FILTER,
            "subdimension": sub,
            "nivel_madurez": nivel
        }).get("payload",{})
        
        new_plan = _as_text(cons.get("plan_intercalado","") or cons.get("plan_pmg","") or cons.get("listado",""))
        if new_plan:
            plan_text = ensure_acciones_alineadas_a_hitos(new_plan, datos_comb, pmg)
        
        # Votación
        print(f"    → Votación del Comité...")
        payload_vote = {"contexto_pm": contexto, "plan_propuesto": plan_text}
        Av = (abo_srv.decide(payload_vote).get("payload",{}) or {}).get("vote","approve")
        Iv = (imp_srv.decide(payload_vote).get("payload",{}) or {}).get("vote","approve")
        Dv = (dev_srv.decide(payload_vote).get("payload",{}) or {}).get("vote","approve")
        
        print(f"      Abogado: {Av}, Implementador: {Iv}, Desarrollador: {Dv}")
        
        if Av == "approve" and Iv == "approve" and Dv == "approve":
            print(f"    ✅ Plan aprobado por unanimidad en ronda {ronda}")
            break
    else:
        print("    ⚠️ Plan finalizado después de 3 rondas (sin consenso total)")
    
    print("\n✅ Plan final generado por el Comité\n")
    print("🎯 FASE 2.5: Generando Indicador de Resultado")
    print("-" * 80)
    print("  → PMG genera indicador de resultado basado en el plan...")
    
    indicador_resultado = generar_indicador_resultado(plan_text, datos_comb, pmg)
    datos_comb['indicador_resultado'] = indicador_resultado
    
    print(f"  ✅ Indicador generado: {indicador_resultado[:100]}{'...' if len(indicador_resultado) > 100 else ''}\n")
    
    # ========== FASE 3: PARSEAR PLAN ==========
    print("\n🔍 FASE 3: Parseando plan...")
    registros = parsear_plan_a_registros(plan_text)
    print(f"  ✅ {len(registros)} actividades/hitos extraídos")
    
    if not registros:
        print("  ⚠️  No se pudo parsear el plan. Se omite actualización.")
        return 0
    
    # ========== FASE 4: ACTUALIZAR BASE DE DATOS ==========
    print("\n💾 FASE 4: Actualizando base de datos...")
    
    # Eliminar plan antiguo
    eliminados = eliminar_plan_antiguo(conn, datos_comb['dimension'], sub, nivel, AUTOR)
    print(f"  → Eliminados {eliminados} registros antiguos")
    
    # Insertar nuevos registros
    for numero, tipo, descripcion in registros:
        insertar_registro(conn, datos_comb, numero, tipo, descripcion)
    
    print(f"  → Insertados {len(registros)} nuevos registros")
    
    # COMMIT
    conn.commit()
    print("  ✅ Transacción confirmada\n")
    
    return len(registros)

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main(nombre_subdimension, nivel_madurez):
    """Función principal que ejecuta el flujo completo para UNA combinación"""
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLAN PTD - SUBDIMENSIÓN + NIVEL ESPECÍFICOS (COMITÉ)")
    print("   Gobernanza de Datos (MGDE) → PostgreSQL")
    print("="*80)
    print(f"📌 Subdimensión: {nombre_subdimension}")
    print(f"📌 Nivel de Madurez: {nivel_madurez}")
    print(f"🔍 ID de grupo de procesos: {GRUPO_PROCESOS}")
    print("="*80 + "\n")
    
    # Conectar a PostgreSQL
    try:
        conn = conectar_db()
        conn.autocommit = False
        print("✅ Conexión establecida con PostgreSQL\n")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
    
    try:
        # Leer datos de la combinación
        datos_comb = leer_datos_combinacion(conn, nombre_subdimension, nivel_madurez)
        
        if not datos_comb:
            print("\n❌ No se pudo continuar. Combinación subdimensión-nivel no existe.")
            print("\n💡 Combinaciones disponibles:")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT Subdimension, Nivel_de_madurez
                FROM ptd_planes
                WHERE Dimension = %s
                  AND Nivel_de_madurez IS NOT NULL
                ORDER BY Subdimension, Nivel_de_madurez
            """, (DIM_FILTER,))
            for subdim, nivel in cursor.fetchall():
                print(f"   • {subdim} - {nivel}")
            cursor.close()
            conn.close()
            return
        
        # Inicializar servidores MCP
        print("🔧 Inicializando servidores MCP...")
        pmg = pmg_srv.PMGServer(grupo_procesos=GRUPO_PROCESOS)
        print("✅ Servidores MCP inicializados\n")
        
        # Procesar combinación
        registros = procesar_combinacion(conn, datos_comb, pmg, abo_srv, imp_srv, dev_srv)
        
        print(f"\n✅ Combinación completada: {registros} registros insertados")
        
        # Verificación final
        print("\n🔍 Verificando plan en base de datos...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Tipo, COUNT(*) as total
            FROM ptd_planes
            WHERE Dimension = %s
              AND Subdimension = %s
              AND Nivel_de_madurez = %s
              AND Autor = %s
            GROUP BY Tipo
            ORDER BY total DESC
        """, (datos_comb['dimension'], datos_comb['subdimension'], datos_comb['nivel_madurez'], AUTOR))
        
        print(f"\n📊 Registros en BD para '{nombre_subdimension}' ({nivel_madurez}):")
        for tipo, total in cursor.fetchall():
            print(f"   • {tipo}: {total} registros")
        
        cursor.close()
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error procesando combinación: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Validar argumentos
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
        print("\nNiveles válidos: Insuficiente, Basico, Medio, Avanzado")
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
