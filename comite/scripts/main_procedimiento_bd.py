#!/usr/bin/env python3
"""
Script Refactorizado: Generación de Planes PTD con Comité - Procedimiento Administrativo
Arquitectura: Multi-agente (Comité) → Generación por subdimensión → Estructura normalizada (filas)
Fecha: 2025-11-10

FLUJO:
1. Sin argumentos - procesa TODAS las subdimensiones
2. Por cada subdimensión:
   - Comité debate y genera plan
   - Se parsea en actividades/hitos individuales
   - Se elimina plan antiguo (autor='Comite')
   - Se insertan nuevas filas
3. Repite para siguiente subdimensión

IDENTIFICACIÓN ÚNICA:
- Procedimiento Administrativo: dimension + subdimension (NO tiene niveles de madurez)
"""
from __future__ import annotations
import sys, os, re
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

def leer_subdimensiones_desde_db(conn):
    """
    Lee las subdimensiones únicas de Procedimiento Administrativo
    
    Returns:
        Lista de diccionarios con los datos de cada subdimensión
    """
    print("\n" + "="*80)
    print("📂 LEYENDO SUBDIMENSIONES DESDE POSTGRESQL")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
    # Usamos DISTINCT ON para tomar una sola fila representativa por subdimensión.
    # Excluimos registros generados por el Comité (Autor='Comite') para no duplicar.
    # Ordenamos priorizando filas con Indicador_Resultado no nulo si existiera.
    sql = """
    SELECT DISTINCT ON (Subdimension)
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
      AND Autor <> %s
    ORDER BY Subdimension, (Indicador_Resultado IS NULL), Indicador_Resultado DESC
    """
    
    try:
        cursor.execute(sql, (DIM_FILTER, AUTOR))
        filas = cursor.fetchall()
        
        subdimensiones = []
        for fila in filas:
            subdimensiones.append({
                'dimension': fila[0],
                'subdimension': fila[1],
                'instrumento': fila[2],
                'indicador': fila[3],
                'brecha': fila[4],
                'pregunta': fila[5],
                'iniciativa': fila[6],
                'objetivo_iniciativa': fila[7],
                'indicador_proceso': fila[8],
                'indicador_resultado': fila[9]
            })

        # Fallback: si la lista está vacía (p.ej. solo existen filas del Comité), quitar filtro Autor y recapturar.
        if not subdimensiones:
            sql_fallback = """
            SELECT DISTINCT ON (Subdimension)
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
            ORDER BY Subdimension, (Indicador_Resultado IS NULL), Indicador_Resultado DESC
            """
            cursor.execute(sql_fallback, (DIM_FILTER,))
            filas_fb = cursor.fetchall()
            for fila in filas_fb:
                subdimensiones.append({
                    'dimension': fila[0],
                    'subdimension': fila[1],
                    'instrumento': fila[2],
                    'indicador': fila[3],
                    'brecha': fila[4],
                    'pregunta': fila[5],
                    'iniciativa': fila[6],
                    'objetivo_iniciativa': fila[7],
                    'indicador_proceso': fila[8],
                    'indicador_resultado': fila[9]
                })
        
        cursor.close()
        
        print(f"📊 Total subdimensiones encontradas: {len(subdimensiones)}")
        for i, sub in enumerate(subdimensiones, 1):
            pregunta_preview = sub.get('pregunta', 'NULL')
            pregunta_str = f" - Pregunta: {pregunta_preview[:50]}..." if pregunta_preview and pregunta_preview != 'NULL' else " - Pregunta: NULL"
            print(f"   {i}. {sub['subdimension']}{pregunta_str}")
        print()
        
        return subdimensiones
        
    except Exception as e:
        print(f"❌ Error leyendo subdimensiones: {e}")
        cursor.close()
        raise

def eliminar_plan_antiguo(conn, dimension, subdimension, autor):
    """
    Elimina los registros antiguos de un plan específico de Procedimiento Administrativo
    
    Args:
        conn: Conexión a PostgreSQL
        dimension: Dimensión del plan
        subdimension: Subdimensión del plan
        autor: Autor del plan ('Comite')
        
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
    
    # Asegurar que indicador_resultado NUNCA sea NULL
    indicador_resultado = datos_fila.get('indicador_resultado')
    if not indicador_resultado or not indicador_resultado.strip():
        # Valor por defecto si no se generó
        contexto = datos_fila.get('pregunta') or datos_fila.get('brecha') or datos_fila['subdimension']
        indicador_resultado = f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"
    
    valores = (
        datos_fila['dimension'],
        datos_fila['subdimension'],
        datos_fila['instrumento'],
        datos_fila['indicador'],
        datos_fila['brecha'],
        None,  # Nivel_de_madurez (NULL para Procedimiento Administrativo)
        None,  # N_Pregunta (NULL)
        datos_fila.get('pregunta'),  # Pregunta - guardar el valor real
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
    
    Formato esperado del Comité:
    1.- Actividad descripción
    HITO 1: Hito descripción
    2.- Actividad descripción
    ...
    
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

def generar_indicador_resultado(plan_text: str, datos_sub: dict, pmg) -> str:
    """
    Genera un Indicador de Resultado usando el servidor PMG
    basado en el plan final generado por el Comité
    """
    try:
        resp = pmg.generate_result_indicator({
            "dimension": DIM_FILTER,
            "subdimension": datos_sub['subdimension'],
            "brecha": datos_sub.get('brecha', ''),
            "pregunta": datos_sub.get('pregunta', ''),
            "respuesta": datos_sub.get('respuesta', 'No'),
            "plan_pmg": plan_text,
            "contexto_pm": "",
            "indicador_prev": "",
            "interv_abogado": "",
            "interv_implementador": "",
            "interv_desarrollador": ""
        })
        indicador = (resp.get("payload") or {}).get("indicador_resultado", "")
        if indicador and indicador.strip():
            return indicador.strip()
    except Exception as e:
        print(f"  ⚠️ Error generando indicador de resultado con PMG: {e}")
    
    # Fallback: usar indicador por defecto
    contexto = datos_sub.get('pregunta') or datos_sub.get('brecha') or datos_sub['subdimension']
    return f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"

def ensure_acciones_alineadas_a_hitos(plan_text: str, datos_sub: dict, pmg) -> str:
    """Asegura que el plan tenga estructura correcta con hitos"""
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

def procesar_subdimension(conn, datos_sub, pmg, abo_srv, imp_srv, dev_srv):
    """
    Procesa UNA subdimensión: debate del Comité → genera plan → inserta en BD
    
    Args:
        conn: Conexión a PostgreSQL
        datos_sub: Dict con datos de la subdimensión
        pmg, abo_srv, imp_srv, dev_srv: Servidores MCP del Comité
        
    Returns:
        Número de registros insertados
    """
    subd = datos_sub['subdimension']
    
    print(f"\n{'='*80}")
    print(f"🤖 PROCESANDO: {subd}")
    print(f"{'='*80}\n")
    
    # FASE 1: Debate de HITOS
    print("📋 FASE 1: Debate de Hitos del Comité")
    print("-" * 80)
    
    prop = pmg.propose_hito({
        "dimension": DIM_FILTER,
        "subdimension": subd,
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
        "contexto_pm": f"Definir 4 HITOS claros y medibles para la subdimensión {subd}.",
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
        "subdimension": subd
    })
    
    final_hitos = enforce_hito_count(hitos)
    print(f"  ✅ {len(final_hitos)} hitos definidos\n")
    
    # FASE 2: Debate de PLAN (3 rondas máximo)
    print("📝 FASE 2: Debate del Plan Completo")
    print("-" * 80)
    
    contexto = (
        f"Plan PTD para {subd}. "
        "Debe tener 4 HITOS obligatorios y 3–4 acciones por cada uno."
    )
    
    print("  → PMG genera plan inicial...")
    init = pmg.generate_initial({
        "dimension": DIM_FILTER,
        "subdimension": subd,
        "hitos_previos": "\\n".join(final_hitos),
        "brecha": datos_sub.get('brecha', ''),
        "pregunta": datos_sub.get('pregunta', ''),
        "respuesta": datos_sub.get('respuesta', 'No'),
        "listado": "",
        "contexto_pm": contexto
    }).get("payload",{})
    
    plan_text = _as_text(init.get("plan_intercalado","") or init.get("plan_pmg","") or init.get("listado",""))
    
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
            "subdimension": subd
        }).get("payload",{})
        
        new_plan = _as_text(cons.get("plan_intercalado","") or cons.get("plan_pmg","") or cons.get("listado",""))
        if new_plan:
            plan_text = ensure_acciones_alineadas_a_hitos(new_plan, datos_sub, pmg)
        
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
    
    # FASE 2.5: Generar Indicador de Resultado
    print("🎯 FASE 2.5: Generando Indicador de Resultado")
    print("-" * 80)
    print("  → PMG genera indicador de resultado basado en el plan...")
    
    indicador_resultado = generar_indicador_resultado(plan_text, datos_sub, pmg)
    datos_sub['indicador_resultado'] = indicador_resultado
    
    print(f"  ✅ Indicador generado: {indicador_resultado[:100]}{'...' if len(indicador_resultado) > 100 else ''}\n")
    
    # FASE 3: Parsear plan a registros individuales
    print("🔧 FASE 3: Parseando plan a estructura normalizada")
    print("-" * 80)
    
    registros = parsear_plan_a_registros(plan_text)
    print(f"  → {len(registros)} elementos parseados")
    print(f"    • Actividades: {sum(1 for r in registros if r[1] == 'Actividad')}")
    print(f"    • Hitos: {sum(1 for r in registros if r[1] == 'Hito')}")
    print()
    
    if not registros:
        print("  ⚠️ No se generaron registros para insertar")
        return 0
    
    # FASE 4: Eliminar plan antiguo e insertar nuevo
    print("💾 FASE 4: Actualizando base de datos")
    print("-" * 80)
    
    # Eliminar plan antiguo del Comité
    eliminados = eliminar_plan_antiguo(conn, datos_sub['dimension'], subd, AUTOR)
    print(f"  → Registros anteriores eliminados: {eliminados}")
    
    # Insertar nuevos registros
    print(f"  → Insertando {len(registros)} nuevos registros...")
    insertados = 0
    
    for numero, tipo, descripcion in registros:
        try:
            insertar_registro(conn, datos_sub, numero, tipo, descripcion)
            insertados += 1
        except Exception as e:
            print(f"    ❌ Error insertando registro {numero}: {e}")
            raise
    
    print(f"  ✅ {insertados} registros insertados correctamente")
    
    # Commit de la transacción
    conn.commit()
    print(f"  ✅ Transacción confirmada\n")
    
    return insertados

def main():
    """Función principal que procesa todas las subdimensiones"""
    print("\n" + "="*80)
    print("🚀 GENERACIÓN DE PLANES PTD CON COMITÉ")
    print("   Procedimiento Administrativo → PostgreSQL")
    print("   Arquitectura: Multi-agente deliberativo")
    print("="*80 + "\n")
    
    # Conectar a base de datos
    print("🔌 Conectando a PostgreSQL...")
    conn = conectar_db()
    print(f"✅ Conectado a: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}\n")
    
    conn.autocommit = False  # Manejar transacciones manualmente
    
    try:
        # Leer todas las subdimensiones
        subdimensiones = leer_subdimensiones_desde_db(conn)
        
        if not subdimensiones:
            print("⚠️ No se encontraron subdimensiones para procesar")
            return
        
        # Importar servidores MCP del Comité
        print("🤖 Inicializando servidores del Comité...")
        pmg = pmg_srv.PMGServer()
        print("✅ Comité listo (PMG, Abogado, Implementador, Desarrollador)\n")
        
        # Procesar cada subdimensión
        total_registros = 0
        subdimensiones_exitosas = 0
        
        for i, datos_sub in enumerate(subdimensiones, 1):
            print(f"\n{'#'*80}")
            print(f"# SUBDIMENSIÓN {i}/{len(subdimensiones)}: {datos_sub['subdimension']}")
            print(f"{'#'*80}")
            
            try:
                registros_insertados = procesar_subdimension(
                    conn, datos_sub, pmg, abo_srv, imp_srv, dev_srv
                )
                total_registros += registros_insertados
                subdimensiones_exitosas += 1
                
            except Exception as e:
                print(f"\n❌ Error procesando subdimensión '{datos_sub['subdimension']}': {e}")
                print("⏭️ Continuando con la siguiente subdimensión...\n")
                conn.rollback()  # Rollback de esta subdimensión
                continue
        
        # Resumen final
        print("\n" + "="*80)
        print("📊 RESUMEN FINAL")
        print("="*80)
        print(f"✅ Subdimensiones procesadas: {subdimensiones_exitosas}/{len(subdimensiones)}")
        print(f"✅ Total registros insertados: {total_registros}")
        print(f"📁 Dimensión: {DIM_FILTER}")
        print(f"👥 Autor: {AUTOR}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("🔌 Conexión cerrada\n")

if __name__ == "__main__":
    main()
