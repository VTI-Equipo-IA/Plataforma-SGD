#!/usr/bin/env python3
"""
Subscript Comité: Generación de Plan PTD para UNA Subdimensión - Procedimiento Administrativo
Procesa una subdimensión específica desde PostgreSQL → Comité debate → Actualiza PostgreSQL
Fecha: 2025-11-10 (Refactorizado 2025-11-20)

USO:
    python generar_plan_subdimension_pa.py "<nombre_subdimension>"
    
    Ejemplo:
    python generar_plan_subdimension_pa.py "Autenticación"
    python generar_plan_subdimension_pa.py "Notificación"

FLUJO (equivalente a script masivo, pero centrado en 1 subdimensión):
1. Recibe nombre de subdimensión como argumento
2. Lee datos (incluye Pregunta y posible Indicador_Resultado previo) desde PostgreSQL
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
DIM_FILTER = "Procedimiento administrativo de función específica"
AUTOR = "Comite"

# Generar ID único para esta ejecución
GRUPO_PROCESOS = f"comite_pa_{uuid.uuid4().hex[:12]}"

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

def ensure_acciones_alineadas_a_hitos(plan_text: str, datos_sub: dict, pmg) -> str:
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
        "subdimension": datos_sub['subdimension'],
        "brecha": datos_sub.get('brecha', ''),
        "pregunta": datos_sub.get('pregunta', ''),
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

def generar_indicador_resultado(plan_text: str, datos_sub: dict, pmg) -> str:
    try:
        resp = pmg.generate_result_indicator({
            "dimension": DIM_FILTER,
            "subdimension": datos_sub['subdimension'],
            "brecha": datos_sub.get('brecha', ''),
            "pregunta": datos_sub.get('pregunta', ''),
            "respuesta": datos_sub.get('respuesta', 'No'),
            "plan_pmg": plan_text,
            "contexto_pm": "",
            "indicador_prev": datos_sub.get('indicador_resultado','') or "",
            "interv_abogado": "",
            "interv_implementador": "",
            "interv_desarrollador": ""
        })
        indicador = (resp.get("payload") or {}).get("indicador_resultado", "")
        if indicador and indicador.strip():
            return indicador.strip()
    except Exception as e:
        print(f"  ⚠️ Error generando indicador de resultado: {e}")
    contexto = datos_sub.get('pregunta') or datos_sub.get('brecha') or datos_sub['subdimension']
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

def leer_datos_subdimension(conn, nombre_subdimension):
    """
    Lee los datos de UNA subdimensión específica desde PostgreSQL
    
    Returns:
        Dict con los datos de la subdimensión o None si no existe
    """
    print("\n" + "="*80)
    print(f"📂 LEYENDO DATOS DE SUBDIMENSIÓN: {nombre_subdimension}")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
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
        Indicador_Proceso,
        Indicador_Resultado
    FROM ptd_planes
    WHERE Dimension = %s
      AND Subdimension = %s
    LIMIT 1
    """
    
    try:
        cursor.execute(sql, (DIM_FILTER, nombre_subdimension))
        fila = cursor.fetchone()
        
        if not fila:
            print(f"❌ No se encontraron datos para la subdimensión '{nombre_subdimension}'")
            cursor.close()
            return None
        
        datos_sub = {
            'dimension': fila[0],
            'subdimension': fila[1],
            'instrumento': fila[2],
            'indicador': fila[3],
            'brecha': fila[4],
            'pregunta': fila[5],
            'iniciativa': fila[6],
            'objetivo_iniciativa': fila[7],
            'indicador_proceso': fila[8],
            'indicador_resultado': fila[9] or ""
        }
        
        cursor.close()
        
        print(f"✅ Datos leídos exitosamente:")
        print(f"   → Dimensión: {datos_sub['dimension']}")
        print(f"   → Subdimensión: {datos_sub['subdimension']}")
        print(f"   → Brecha: {datos_sub['brecha'][:100]}...")
        print(f"   → Pregunta: {(datos_sub.get('pregunta') or 'NULL')[:100]}")
        prev_ind = datos_sub.get('indicador_resultado')
        if prev_ind:
            print(f"   → Indicador Resultado previo (preview): {prev_ind[:80]}{'...' if len(prev_ind)>80 else ''}")
        print()
        
        return datos_sub
        
    except Exception as e:
        print(f"❌ Error leyendo subdimensión: {e}")
        cursor.close()
        raise

def eliminar_plan_antiguo(conn, dimension, subdimension, autor):
    """Elimina los registros antiguos de un plan específico"""
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
    
    indicador_resultado = datos_fila.get('indicador_resultado')
    if not indicador_resultado or not str(indicador_resultado).strip():
        contexto = datos_fila.get('pregunta') or datos_fila.get('brecha') or datos_fila['subdimension']
        indicador_resultado = f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"
    valores = (
        datos_fila['dimension'],
        datos_fila['subdimension'],
        datos_fila['instrumento'],
        datos_fila['indicador'],
        datos_fila['brecha'],
        None,  # Nivel_de_madurez (NULL para PA)
        None,  # N_Pregunta (NULL para PA)
        datos_fila.get('pregunta'),  # Pregunta real (puede ser NULL)
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

def procesar_subdimension(conn, datos_sub, pmg, abo_srv, imp_srv, dev_srv):
    """
    Procesa una subdimensión y genera plan con el Comité
    
    FASE 1: Debate de HITOS (4 obligatorios)
    FASE 2: Debate de PLAN (3 rondas máximo)
    FASE 3: Parsear plan en actividades/hitos
    FASE 4: Eliminar plan antiguo + Insertar nuevos registros
    
    Returns:
        Número de registros insertados
    """
    sub = datos_sub['subdimension']
    
    print("\n" + "="*80)
    print(f"🔹 PROCESANDO: {sub}")
    print("="*80)
    
    # ========== FASE 1: DEBATE DE HITOS ==========
    print("\n📍 FASE 1: Debate de HITOS")
    print("-" * 80)
    
    # Incluir brecha y pregunta para que el servidor PMG tenga suficiente contexto.
    prop = pmg.propose_hito({
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "brecha": datos_sub.get('brecha', ''),
        "pregunta": datos_sub.get('pregunta', ''),
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
        "contexto_pm": f"Definir 4 HITOS claros y medibles para la subdimensión {sub}.",
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
        "subdimension": sub
    })
    
    final_hitos = enforce_hito_count(hitos)
    print(f"  ✅ {len(final_hitos)} hitos definidos\n")
    
    # ========== FASE 2: DEBATE DE PLAN ==========
    print("\n📝 FASE 2: Debate de PLAN")
    contexto_plan = (
        f"Plan para {sub}. "
        "Debe tener 4 HITOS obligatorios y 3–4 acciones por cada uno."
    )
    
    init = pmg.generate_initial({
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "hitos_previos": "\n".join(final_hitos),
        "brecha": datos_sub.get('brecha',''),
        "pregunta": datos_sub.get('pregunta',''),
        "respuesta": datos_sub.get('respuesta','No'),
        "listado": "",
        "contexto_pm": contexto_plan
    }).get("payload",{})
    
    plan_text = _as_text(
        init.get("plan_intercalado","") or 
        init.get("plan_pmg","") or 
        init.get("listado","")
    )
    
    print(f"  → PMG generó plan inicial ({len(plan_text)} chars)")
    
    # Hasta 3 rondas de debate
    for ronda in range(1, 4):
        print(f"\n  🔄 Ronda {ronda}/3")
        
        inter_payload = {
            "contexto_pm": contexto_plan,
            "listado_vigente": plan_text
        }
        
        Ai = _as_text((abo_srv.intervention(inter_payload).get("payload",{}) or {}).get("intervencion",""))
        Ii = _as_text((imp_srv.intervention(inter_payload).get("payload",{}) or {}).get("intervencion",""))
        Di = _as_text((dev_srv.intervention(inter_payload).get("payload",{}) or {}).get("intervencion",""))
        
        print("     → Agentes intervinieron")
        
        cons = pmg.consolidate_select({
            "hitos_previos": "\n".join(final_hitos),
            "plan_pmg": plan_text,
            "interv_abogado": Ai,
            "interv_implementador": Ii,
            "interv_desarrollador": Di,
            "dimension": DIM_FILTER,
            "subdimension": sub
        }).get("payload",{})
        
        new_plan = _as_text(
            cons.get("plan_intercalado","") or 
            cons.get("plan_pmg","") or 
            cons.get("listado","")
        )
        
        if new_plan:
            plan_text = ensure_acciones_alineadas_a_hitos(new_plan, datos_sub, pmg)
        
        print("     → PMG consolidó")
        
        # Votación
        payload_vote = {
            "contexto_pm": contexto_plan,
            "plan_propuesto": plan_text
        }
        
        Av = (abo_srv.decide(payload_vote).get("payload",{}) or {}).get("vote","approve")
        Iv = (imp_srv.decide(payload_vote).get("payload",{}) or {}).get("vote","approve")
        Dv = (dev_srv.decide(payload_vote).get("payload",{}) or {}).get("vote","approve")
        
        print(f"     → Votos: Abogado={Av}, Implementador={Iv}, Desarrollador={Dv}")
        
        if Av == "approve" and Iv == "approve" and Dv == "approve":
            print("     ✅ ¡Aprobación unánime!")
            break
    
    print(f"\n  ✅ Plan final aprobado ({len(plan_text)} chars)")

    # ========== FASE 2.5: INDICADOR DE RESULTADO ==========
    print("\n🎯 FASE 2.5: Generando Indicador de Resultado")
    indicador_resultado = generar_indicador_resultado(plan_text, datos_sub, pmg)
    datos_sub['indicador_resultado'] = indicador_resultado
    print(f"  ✅ Indicador Resultado: {indicador_resultado[:100]}{'...' if len(indicador_resultado)>100 else ''}")
    
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
    eliminados = eliminar_plan_antiguo(conn, datos_sub['dimension'], sub, AUTOR)
    print(f"  → Eliminados {eliminados} registros antiguos")
    
    # Insertar nuevos registros
    for numero, tipo, descripcion in registros:
        insertar_registro(conn, datos_sub, numero, tipo, descripcion)
    
    print(f"  → Insertados {len(registros)} nuevos registros")
    
    # COMMIT
    conn.commit()
    print("  ✅ Transacción confirmada\n")
    
    return len(registros)

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main(nombre_subdimension):
    """Función principal que ejecuta el flujo completo para UNA subdimensión"""
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLAN PTD - SUBDIMENSIÓN ESPECÍFICA (COMITÉ)")
    print("   Procedimiento Administrativo → PostgreSQL")
    print("="*80)
    print(f"📌 Subdimensión a procesar: {nombre_subdimension}")
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
        # Leer datos de la subdimensión
        datos_sub = leer_datos_subdimension(conn, nombre_subdimension)
        
        if not datos_sub:
            print("\n❌ No se pudo continuar. La subdimensión no existe en la base de datos.")
            print("\n💡 Subdimensiones disponibles:")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT Subdimension
                FROM ptd_planes
                WHERE Dimension = %s
                ORDER BY Subdimension
            """, (DIM_FILTER,))
            for (subdim,) in cursor.fetchall():
                print(f"   • {subdim}")
            cursor.close()
            conn.close()
            return
        
        # Inicializar servidores MCP
        print("🔧 Inicializando servidores MCP...")
        pmg = pmg_srv.PMGServer(grupo_procesos=GRUPO_PROCESOS)
        print("✅ Servidores MCP inicializados\n")
        
        # Procesar subdimensión
        registros = procesar_subdimension(conn, datos_sub, pmg, abo_srv, imp_srv, dev_srv)
        
        print(f"\n✅ Subdimensión completada: {registros} registros insertados")
        
        # Verificación final
        print("\n🔍 Verificando plan en base de datos...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Tipo, COUNT(*) as total
            FROM ptd_planes
            WHERE Dimension = %s
              AND Subdimension = %s
              AND Autor = %s
            GROUP BY Tipo
            ORDER BY total DESC
        """, (datos_sub['dimension'], datos_sub['subdimension'], AUTOR))
        
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
