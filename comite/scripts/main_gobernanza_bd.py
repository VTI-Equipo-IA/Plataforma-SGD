#!/usr/bin/env python3
"""
Script Refactorizado: Generación de Planes PTD con Comité - Gobernanza de Datos
Arquitectura: Multi-agente (Comité) → Generación por subdimensión+nivel → Estructura normalizada
Fecha: 2025-11-10

FLUJO:
1. Sin argumentos - procesa TODAS las combinaciones (subdimensión + nivel_madurez)
2. Por cada combinación:
   - Comité debate y genera plan
   - Se parsea en actividades/hitos individuales
   - Se elimina plan antiguo (autor='Comite')
   - Se insertan nuevas filas
3. Repite para siguiente combinación

IDENTIFICACIÓN ÚNICA:
- Gobernanza de Datos: dimension + subdimension + nivel_de_madurez
- Niveles: Insuficiente, Basico, Medio, Avanzado
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
DIM_FILTER = "Gobernanza de datos"
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

def leer_combinaciones_desde_db(conn):
    """
    Lee todas las combinaciones únicas de subdimensión + nivel de madurez
    
    Returns:
        Lista de diccionarios con los datos de cada combinación
    """
    print("\n" + "="*80)
    print("📂 LEYENDO COMBINACIONES (SUBDIMENSIÓN + NIVEL) DESDE POSTGRESQL")
    print("="*80 + "\n")
    
    cursor = conn.cursor()
    
    # Primero, obtener las combinaciones únicas de subdimensión + nivel
    sql_combinaciones = """
    SELECT DISTINCT
        Subdimension,
        Nivel_de_madurez
    FROM ptd_planes
    WHERE Dimension = %s
      AND Nivel_de_madurez IS NOT NULL
    ORDER BY Subdimension, Nivel_de_madurez
    """
    
    try:
        cursor.execute(sql_combinaciones, (DIM_FILTER,))
        combinaciones_unicas = cursor.fetchall()
        
        # Para cada combinación única, obtener los datos adicionales (tomando el primer registro)
        combinaciones = []
        sql_detalle = """
        SELECT 
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
        
        for subdim, nivel in combinaciones_unicas:
            cursor.execute(sql_detalle, (DIM_FILTER, subdim, nivel))
            fila = cursor.fetchone()
            if fila:
                combinaciones.append({
                    'dimension': fila[0],
                    'subdimension': fila[1],
                    'instrumento': fila[2],
                    'indicador': fila[3],
                    'brecha': fila[4],
                    'nivel_de_madurez': fila[5],
                    'iniciativa': fila[6],
                    'objetivo_iniciativa': fila[7],
                    'indicador_proceso': fila[8],
                    'indicador_resultado': fila[9]
                })
        
        cursor.close()
        
        print(f"📊 Total combinaciones encontradas: {len(combinaciones)}")
        
        # Agrupar por subdimensión para mostrar resumen
        subdims = {}
        for comb in combinaciones:
            sub = comb['subdimension']
            nivel = comb['nivel_de_madurez']
            if sub not in subdims:
                subdims[sub] = []
            subdims[sub].append(nivel)
        
        for i, (sub, niveles) in enumerate(subdims.items(), 1):
            ind_res_preview = combinaciones[0].get('indicador_resultado', 'NULL') if combinaciones else 'NULL'
            ind_res_str = f" | Ind.Res: {ind_res_preview[:40]}..." if ind_res_preview and ind_res_preview != 'NULL' else " | Ind.Res: NULL"
            print(f"   {i}. {sub}: {', '.join(niveles)}{ind_res_str}")
        print()
        
        return combinaciones
        
    except Exception as e:
        print(f"❌ Error leyendo combinaciones: {e}")
        cursor.close()
        raise

def eliminar_plan_antiguo(conn, dimension, subdimension, nivel_madurez, autor):
    """
    Elimina los registros antiguos de un plan específico de Gobernanza
    
    Args:
        conn: Conexión a PostgreSQL
        dimension: Dimensión del plan
        subdimension: Subdimensión del plan
        nivel_madurez: Nivel de madurez del plan
        autor: Autor del plan ('Comite')
        
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
    
    # Asegurar que indicador_resultado NUNCA sea NULL
    indicador_resultado = datos_fila.get('indicador_resultado')
    if not indicador_resultado or not indicador_resultado.strip():
        # Valor por defecto si no se generó
        contexto = f"{datos_fila['subdimension']} - Nivel {datos_fila['nivel_de_madurez']}"
        indicador_resultado = f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"
    
    valores = (
        datos_fila['dimension'],
        datos_fila['subdimension'],
        datos_fila['instrumento'],
        datos_fila['indicador'],
        datos_fila['brecha'],
        datos_fila['nivel_de_madurez'],  # IMPORTANTE: Gobernanza SÍ tiene nivel
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
    Si hay menos, genera hitos genéricos
    Si hay más, toma los primeros n_required
    """
    if not hitos:
        return []
    
    nh = len(hitos)
    if nh == n_required:
        return hitos
    elif nh < n_required:
        print(f"  ⚠️  Solo hay {nh} hitos. Se completará hasta {n_required}.")
        # Completar con hitos genéricos
        stages = [
            "Configuración técnica completada en ambiente de pruebas",
            "Pruebas/certificación superadas",
            "En producción con seguimiento básico",
            "Brecha cerrada y verificación documentada",
        ]
        completed = list(hitos)
        while len(completed) < n_required:
            idx = len(completed)
            completed.append(f"HITO {idx+1}: {stages[idx]}")
        return completed
    else:
        print(f"  ⚠️  Hay {nh} hitos. Se tomarán solo los primeros {n_required}.")
        return hitos[:n_required]

def generar_indicador_resultado(plan_text: str, datos_comb: dict, pmg) -> str:
    """
    Genera un Indicador de Resultado usando el servidor PMG
    basado en el plan final generado por el Comité
    """
    try:
        resp = pmg.generate_result_indicator({
            "dimension": DIM_FILTER,
            "subdimension": datos_comb['subdimension'],
            "nivel_madurez": datos_comb['nivel_de_madurez'],
            "brecha": datos_comb.get('brecha', ''),
            "pregunta": "",  # Gobernanza no tiene pregunta
            "respuesta": datos_comb.get('respuesta', 'No'),
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
    contexto = f"{datos_comb['subdimension']} - Nivel {datos_comb['nivel_de_madurez']}"
    return f"Porcentaje de cumplimiento de {contexto} verificado con evidencia documental"

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

def procesar_combinacion(conn, datos_comb, pmg, abo_srv, imp_srv, dev_srv):
    """
    Procesa una combinación (subdimensión + nivel) y genera plan
    
    FASE 1: Debate de HITOS (4 obligatorios)
    FASE 2: Debate de PLAN (3 rondas máximo)
    FASE 3: Parsear plan en actividades/hitos
    FASE 4: Eliminar plan antiguo + Insertar nuevos registros
    
    Returns:
        Número de registros insertados
    """
    sub = datos_comb['subdimension']
    nivel = datos_comb['nivel_de_madurez']
    
    print("\n" + "="*80)
    print(f"🔹 PROCESANDO: {sub} - Nivel: {nivel}")
    print("="*80)
    
    # ========== FASE 1: DEBATE DE HITOS ==========
    print("\n📍 FASE 1: Debate de HITOS")
    contexto_hitos = f"Definir 4 HITOS claros y medibles para avanzar desde el nivel {nivel}."
    
    print("  → PMG propone hitos iniciales...")
    
    # DEBUG: Mostrar parámetros enviados a PMG
    # Agregar contexto de nivel en el listado para ayudar a PMG
    contexto_listado = f"Plan para avanzar desde nivel {nivel} en {sub}. Generar 4 hitos claros y medibles."
    
    params_hito = {
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "brecha": datos_comb.get('brecha', ''),
        "pregunta": f"¿Cómo avanzar desde nivel {nivel} hacia el siguiente nivel?",
        "listado": contexto_listado,
    }
    print(f"  🔍 DEBUG - Parámetros para propose_hito:")
    print(f"     dimension: {params_hito['dimension']}")
    print(f"     subdimension: {params_hito['subdimension']}")
    print(f"     pregunta: {params_hito['pregunta']}")
    print(f"     brecha: {params_hito['brecha'][:80]}..." if params_hito['brecha'] else "     brecha: (vacío)")
    print(f"     listado: {params_hito['listado']}")
    
    try:
        prop = pmg.propose_hito(params_hito)
        
        # DEBUG: Mostrar respuesta completa de PMG
        print(f"  🔍 DEBUG - Respuesta de propose_hito:")
        print(f"     status: {prop.get('status', 'N/A')}")
        
        hitos = []
        
        # Si hay error, intentar parsear la respuesta raw directamente
        if prop.get('status') == 'error' and 'raw' in prop:
            print(f"     ⚠️  Error en JSON, intentando parsear respuesta raw...")
            raw_response = prop.get('raw', '')
            
            # Limpiar markdown code blocks
            import json
            cleaned = raw_response.strip()
            if cleaned.startswith('```'):
                # Remover ```json o ``` del inicio
                lines = cleaned.split('\n')
                lines = [l for l in lines if not l.strip().startswith('```')]
                cleaned = '\n'.join(lines).strip()
            
            try:
                # Intentar parsear el JSON limpio
                data = json.loads(cleaned)
                print(f"     ✅ JSON parseado exitosamente después de limpiar")
                
                # Extraer hitos
                if isinstance(data, list):
                    for h in data:
                        if isinstance(h, dict):
                            hitos.append(h.get("texto", ""))
                        else:
                            hitos.append(str(h))
            except Exception as e2:
                print(f"     ❌ No se pudo parsear JSON limpio: {e2}")
                print(f"     raw (primeros 300 chars): {cleaned[:300]}...")
        else:
            # Respuesta OK, procesar normalmente
            print(f"     payload keys: {list((prop.get('payload') or {}).keys())}")
            raw_h = (prop.get("payload") or {}).get("hitos") or []
            for h in raw_h:
                if isinstance(h, dict):
                    hitos.append(h.get("texto",""))
                else:
                    hitos.append(str(h))
        
        print(f"  → PMG propuso {len(hitos)} hitos")
        
    except Exception as e:
        print(f"  ❌ Excepción en propose_hito: {e}")
        import traceback
        traceback.print_exc()
        hitos = []
    
    # Intervenciones de agentes
    payload_h = {
        "contexto_pm": contexto_hitos,
        "listado_vigente": "\n".join(hitos)
    }
    
    A = _as_text((abo_srv.intervention(payload_h).get("payload",{}) or {}).get("intervencion",""))
    I = _as_text((imp_srv.intervention(payload_h).get("payload",{}) or {}).get("intervencion",""))
    D = _as_text((dev_srv.intervention(payload_h).get("payload",{}) or {}).get("intervencion",""))
    
    print("  → Agentes intervinieron")
    
    print("  → PMG consolida intervenciones...")
    # PMG consolida
    pmg.consolidate_select({
        "plan_pmg": "\n".join(hitos) if hitos else "",
        "interv_abogado": A,
        "interv_implementador": I,
        "interv_desarrollador": D,
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "nivel_madurez": nivel
    })
    
    # Si no hay hitos, generar 4 hitos genéricos
    if not hitos or len(hitos) == 0:
        print("  ⚠️  No se generaron hitos. Usando hitos genéricos...")
        hitos = [
            f"HITO 1: Configuración técnica completada para {sub} en ambiente de pruebas",
            f"HITO 2: Pruebas y certificación superadas para nivel {nivel}",
            f"HITO 3: Sistema en producción con seguimiento básico",
            f"HITO 4: Nivel {nivel} alcanzado y verificado con evidencia documental"
        ]
    
    final_hitos = enforce_hito_count(hitos, 4)
    print(f"  ✅ {len(final_hitos)} hitos definidos")
    
    # ========== FASE 2: DEBATE DE PLAN ==========
    print("\n📝 FASE 2: Debate de PLAN")
    contexto_plan = (
        f"Plan de gobernanza para avanzar desde el nivel {nivel}. "
        "Debe tener 4 HITOS obligatorios y 3–4 acciones por cada uno."
    )
    
    # Usar consolidate_select directamente con los hitos previos para generar plan inicial
    # Este método está diseñado para generar un plan intercalado correctamente
    init_cons = pmg.consolidate_select({
        "hitos_previos": "\n".join(final_hitos),
        "plan_pmg": "",  # Vacío para que genere desde cero
        "interv_abogado": "",
        "interv_implementador": "",
        "interv_desarrollador": "",
        "dimension": DIM_FILTER,
        "subdimension": sub,
        "nivel_madurez": nivel,
        "brecha": datos_comb.get('brecha', ''),
        "pregunta": "",
        "respuesta": "No"
    }).get("payload", {})
    
    # DEBUG: Ver qué devuelve consolidate_select inicial
    print(f"  🔍 DEBUG - consolidate_select inicial devolvió:")
    print(f"     plan_intercalado: {len(init_cons.get('plan_intercalado',''))} chars")
    print(f"     plan_pmg: {len(init_cons.get('plan_pmg',''))} chars")
    print(f"     listado: {len(str(init_cons.get('listado','')))} chars")
    
    plan_text = _as_text(
        init_cons.get("plan_intercalado","") or 
        init_cons.get("plan_pmg","") or 
        "\n".join(init_cons.get("listado",[]))
    )
    
    print(f"  → PMG generó plan inicial ({len(plan_text)} chars)")
    print(f"  🔍 DEBUG - Plan inicial completo:")
    print(f"  {'─'*76}")
    print(f"  {plan_text}")
    print(f"  {'─'*76}\n")
    
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
            "subdimension": sub,
            "nivel_madurez": nivel
        }).get("payload",{})
        
        # DEBUG: Ver qué devuelve consolidate_select
        print(f"     🔍 DEBUG - consolidate_select devolvió:")
        print(f"        plan_intercalado: {len(cons.get('plan_intercalado',''))} chars")
        print(f"        plan_pmg: {len(cons.get('plan_pmg',''))} chars")
        print(f"        listado: {len(cons.get('listado',''))} chars")
        
        new_plan = _as_text(
            cons.get("plan_intercalado","") or 
            cons.get("plan_pmg","") or 
            cons.get("listado","")
        )
        
        print(f"     🔍 DEBUG - new_plan seleccionado: {len(new_plan)} chars")
        
        if new_plan:
            plan_text = ensure_acciones_alineadas_a_hitos(new_plan, "\n".join(final_hitos))
        
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
    
    print(f"  ✅ Plan final aprobado ({len(plan_text)} chars)")
    
    # DEBUG: Mostrar contenido del plan final
    print(f"\n  🔍 DEBUG - Plan final completo:")
    print(f"  {'─'*76}")
    print(f"  {plan_text}")
    print(f"  {'─'*76}\n")
    
    # ========== FASE 2.5: GENERAR INDICADOR DE RESULTADO ==========
    print("\n🎯 FASE 2.5: Generando Indicador de Resultado")
    print("  → PMG genera indicador de resultado basado en el plan...")
    
    indicador_resultado = generar_indicador_resultado(plan_text, datos_comb, pmg)
    datos_comb['indicador_resultado'] = indicador_resultado
    
    print(f"  ✅ Indicador generado: {indicador_resultado[:100]}{'...' if len(indicador_resultado) > 100 else ''}")
    
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


def main():
    """
    Función principal: Itera todas las combinaciones (subdimensión + nivel)
    y genera planes con el Comité
    """
    print("\n" + "="*80)
    print("🚀 INICIO: Generación de Planes PTD - Gobernanza de Datos (Comité)")
    print("="*80)
    
    # Conectar a PostgreSQL
    try:
        conn = conectar_db()
        conn.autocommit = False  # Transacciones manuales
        print("✅ Conexión establecida con PostgreSQL\n")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
    
    # Leer todas las combinaciones
    try:
        combinaciones = leer_combinaciones_desde_db(conn)
    except Exception as e:
        print(f"❌ Error leyendo combinaciones: {e}")
        conn.close()
        sys.exit(1)
    
    if not combinaciones:
        print("⚠️  No se encontraron combinaciones para procesar.")
        conn.close()
        return
    
    # Inicializar servidores MCP
    print("🔧 Inicializando servidores MCP...")
    pmg = pmg_srv.PMGServer()
    print("✅ Servidores MCP inicializados\n")
    
    # Procesar cada combinación
    total_registros = 0
    total_procesadas = 0
    total_fallidas = 0
    
    for i, datos_comb in enumerate(combinaciones, 1):
        sub = datos_comb['subdimension']
        nivel = datos_comb['nivel_de_madurez']
        
        print(f"\n{'='*80}")
        print(f"📦 Combinación {i}/{len(combinaciones)}: {sub} - {nivel}")
        print(f"{'='*80}")
        
        try:
            registros = procesar_combinacion(conn, datos_comb, pmg, abo_srv, imp_srv, dev_srv)
            total_registros += registros
            total_procesadas += 1
            print(f"✅ Combinación {i} completada: {registros} registros insertados")
            
        except Exception as e:
            total_fallidas += 1
            print(f"\n❌ ERROR en combinación {i} ({sub} - {nivel}):")
            print(f"   {str(e)}")
            print("   → Revirtiendo transacción...")
            conn.rollback()
            print("   → Continuando con siguiente combinación\n")
            continue
    
    # Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    print(f"✅ Combinaciones procesadas: {total_procesadas}/{len(combinaciones)}")
    print(f"❌ Combinaciones fallidas: {total_fallidas}")
    print(f"📝 Total registros insertados: {total_registros}")
    print(f"📊 Promedio registros/combinación: {total_registros/total_procesadas if total_procesadas > 0 else 0:.1f}")
    print("="*80 + "\n")
    
    conn.close()
    print("🔌 Conexión cerrada")
    print("✨ Proceso completado\n")


if __name__ == "__main__":
    main()
