# mcp/servers/mcp_server_pmg.py
from __future__ import annotations
import os, json, re, unicodedata, sys
from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Importar helper de tracking
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from comite.utils.tracked_llm_mcp import create_mcp_llm

# ---------------- Config ----------------
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Temperaturas (puedes fijarlas aquí si quieres eliminar getenv)
TEMP_INIT   = float(os.getenv("PMG_TEMP_INIT", "0.25"))
TEMP_CONS   = float(os.getenv("PMG_TEMP_CONS", "0.25"))
TEMP_TITLE  = float(os.getenv("PMG_TEMP_TITLE", "0.2"))
TEMP_HITO   = float(os.getenv("PMG_TEMP_HITO", "0.2"))

MAXTOK_INIT  = int(os.getenv("PMG_MAXTOK_INIT", "700"))
MAXTOK_CONS  = int(os.getenv("PMG_MAXTOK_CONS", "1100"))
MAXTOK_TITLE = int(os.getenv("PMG_MAXTOK_TITLE", "120"))
MAXTOK_HITO  = int(os.getenv("PMG_MAXTOK_HITO", "400"))

INDICES_DIR = os.getenv("PMG_INDEX_DIR", "indices/pmg_index")
EMB_MODEL   = os.getenv("PMG_EMB_MODEL", "text-embedding-3-small")

# ---------------- Utilidades locales ----------------

# Patrón para detectar "HITO N:"
RE_HITO = re.compile(r"^\s*HITO\s*\d*\s*:\s*", flags=re.IGNORECASE)
# Quitar "Plan de mejora:" si llegara
RE_PLAN = re.compile(r"^\s*plan\s+de\s+mejora\s*:\s*", flags=re.IGNORECASE)
# Numeradores "1. " / "2) "
_NUM_RE = re.compile(r"^\s*\d+\s*[\.\)]\s*")
# Listas literales con comillas simples
RE_QUOTED_ITEM  = re.compile(r"^\s*'(.+?)'\s*$")
_TITLE_PAT = re.compile(r"\*\*(.*?)\*\*")  # negritas markdown

def _llm(temp: float, max_tokens: Optional[int] = None, grupo_procesos: Optional[str] = None) -> ChatOpenAI:
    """Crea LLM con tracking automático de consumo."""
    return create_mcp_llm(
        model=OPENAI_MODEL,
        temperature=temp,
        app_name="PMG",
        max_tokens=max_tokens,
        grupo_procesos=grupo_procesos,
        track_enabled=True
    )

def _strip_accents(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def _as_lines(x) -> list[str]:
    """Convierte entrada (texto/lista) a lista de líneas no vacías."""
    if x is None: return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    return [ln.strip() for ln in str(x).splitlines() if str(ln).strip()]

def _is_hito(line: str) -> bool:
    return bool(re.match(r"^\s*HITO\s+\d+\s*:\s*", line or "", flags=re.IGNORECASE))

def _strip_action_titles(line: str) -> str:
    """Quita negritas y cabeceras tipo 'Título: ...' dejando solo la acción."""
    if not line: return ""
    s = str(line).strip()
    s = _NUM_RE.sub("", s).strip()             # quita numeradores
    s = _TITLE_PAT.sub(r"\1", s)               # quita **negritas**
    if ":" in s:                               # separador de “Título: acción”
        left, right = s.split(":", 1)
        if len(left.split()) <= 5:
            s = right.strip()
    s = RE_HITO.sub("", s)                     # no debe empezar como HITO
    s = re.sub(r"\s+", " ", s).strip(" .;-")
    return s

def _norm_key(s: str) -> str:
    """Clave robusta para de-duplicado de acciones."""
    s = s or ""
    s = RE_PLAN.sub("", s)
    s = RE_HITO.sub("", s)
    s = _NUM_RE.sub("", s)
    s = _strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9ñáéíóúü\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _clean_action_lines(text_or_list: Any) -> list[str]:
    """Convierte a líneas y limpia títulos/negritas; descarta duplicados; preserva HITO."""
    lines = _as_lines(text_or_list)
    out, seen = [], set()
    for ln in lines:
        if _is_hito(ln):
            k = f"H|{ln.strip().lower()}"
            if k not in seen:
                out.append(ln.strip()); seen.add(k)
            continue
        body = _strip_action_titles(ln)
        if not body: 
            continue
        k = f"A|{_norm_key(body)}"
        if k not in seen:
            out.append(body); seen.add(k)
    return out

def _flatten_plan_lines(text: str) -> list[str]:
    """Aplana listas-literal (['a','b']) y limpia comillas/negritas/':'. Una línea por ítem."""
    lines = _as_lines(text)
    out = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1]
            parts = re.split(r"',\s*'", inner.strip("'"))
            out.extend([p.strip() for p in parts if p.strip()])
        else:
            m = RE_QUOTED_ITEM.match(s)
            out.append(m.group(1) if m else s)
    # limpieza
    cleaned = []
    for ln in out:
        if _is_hito(ln):
            cleaned.append(re.sub(r"\s+", " ", ln).strip())
        else:
            body = _strip_action_titles(ln)
            if body:
                cleaned.append(body)
    # de-duplicado preservando orden
    seen = set(); dedup = []
    for ln in cleaned:
        key = _norm_key(ln)
        if key not in seen:
            dedup.append(ln); seen.add(key)
    return dedup

def _ensure_one_hito(lines: list[str], pregunta: str = "") -> list[str]:
    """Si no hay HITO, agrega uno genérico al final."""
    if any(_is_hito(ln) for ln in lines):
        return lines
    if not pregunta:
        cierre = "HITO 1: Cierre de la brecha logrado."
    else:
        pregunta_limpia = re.sub(r'\s+', ' ', pregunta).strip().rstrip('.')
        cierre = f"HITO 1: {pregunta_limpia}: en operación y verificado."
    return lines + [cierre]

def _normalize_numbered_plan(text: str, hitos: List[str]) -> str:
    if not text: return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: List[str] = []
    n = 1
    for ln in lines:
        if _is_hito(ln): out.append(ln)
        else:
            body = _NUM_RE.sub("", ln).strip()
            body = RE_PLAN.sub("", body)
            out.append(f"{n}.- {body}"); n += 1
    if hitos and out and not _is_hito(out[-1]):  # último renglón debe ser HITO
        last = hitos[-1]
        if not _is_hito(last):
            last_limpio = re.sub(r'^HITO\s*\d*\s*:\s*','',last,flags=re.IGNORECASE).strip(': -')
            last = f"HITO {len(hitos)}: {last_limpio}"
        out.append(last)
    return "\n".join(out)

def _force_newlines(text: str) -> str:
    """Garantiza que cada ítem vaya en línea propia."""
    return "\n".join(_as_lines(text))

def _clip_extra_hitos_in_plan(plan_lines: list[str], dim: str) -> list[str]:
    """Elimina HITO extra (>target) y asegura terminar en el último válido."""
    target = 1 if "calidad web" in (dim or "").lower() else 4
    out, count = [], 0
    for ln in plan_lines:
        if _is_hito(ln):
            count += 1
            if count > target: continue
        out.append(ln)
    if out and not _is_hito(out[-1]):
        last = [x for x in out if _is_hito(x)]
        if last: out.append(last[-1])
    return out

# Plantillas de hitos concretos (no “logro intermedio”)
def _mk_base_from_ctx(p: Dict[str,Any]) -> str:
    q = (p.get("pregunta","") or "").strip().rstrip(".")
    b = (p.get("brecha","") or "").strip().rstrip(".")
    sub = (p.get("subdimension","") or "").strip()
    if q: return q
    if b: return b
    return sub or "Logro"

def _stage_hitos_for_dim(p: Dict[str,Any], target:int) -> list[str]:
    base = _mk_base_from_ctx(p)
    dim  = (p.get("dimension","") or "").lower()
    if "calidad web" in dim:
        return [f"{base}: en operación y verificado (brecha cerrada)"]
    return [
        f"{base}: configuración técnica completada en ambiente de pruebas",
        f"{base}: integración/pruebas/certificación superadas",
        f"{base}: habilitado en producción con seguimiento básico",
        f"{base}: brecha cerrada y verificación documentada"
    ][:target]

def _enforce_hito_count_by_dim(dim: str, hitos: list[str], p: Dict[str,Any]=None) -> list[str]:
    """Exactamente 4 hitos en Proc/Gob; 1 en Calidad web. Completa con plantillas contextuales."""
    target = 1 if "calidad web" in (dim or "").lower() else 4
    fixed=[]; n=1
    for h in hitos:
        s = re.sub(r"^\s*HITO\s*\d*\s*:\s*", "", str(h), flags=re.IGNORECASE).strip(": -")
        if s:
            fixed.append(f"HITO {n}: {s}"); n += 1
    if len(fixed) > target:
        fixed = fixed[:target]
    if len(fixed) < target:
        stages = _stage_hitos_for_dim(p or {}, target)
        i0 = len(fixed)
        for idx in range(i0, target):
            fixed.append(f"HITO {idx+1}: {stages[idx]}")
    out=[]; n=1
    for h in fixed:
        s = re.sub(r"^\s*HITO\s*\d*\s*:\s*", "", h, flags=re.IGNORECASE).strip(": -")
        out.append(f"HITO {n}: {s}"); n += 1
    return out

# Acción mínima para HITO sin acciones previas
def _minimal_action_for_hito(hito_text:str) -> str:
    s = re.sub(r"^\s*HITO\s*\d+\s*:\s*", "", hito_text, flags=re.IGNORECASE).strip().lower()
    if ("pruebas" in s) or ("certificación" in s) or ("certificacion" in s):
        return "Ejecutar pruebas técnicas y registrar evidencia de certificación"
    if ("producción" in s) or ("produccion" in s) or ("habilitado" in s):
        return "Habilitar la funcionalidad en producción y activar monitoreo básico"
    if ("verificación" in s) or ("verificacion" in s) or ("brecha cerrada" in s) or ("cerrada" in s):
        return "Registrar verificación de cierre con evidencia mínima y acta interna"
    if ("configuración" in s) or ("configuracion" in s) or ("ambiente de pruebas" in s):
        return "Configurar integración en ambiente de pruebas según manual vigente"
    return "Realizar la acción mínima necesaria para materializar el logro descrito"

def _ensure_actions_before_each_hito(plan_lines: list[str]) -> list[str]:
    """Para cada HITO, si no hay acción inmediata previa, inyecta una acción mínima coherente."""
    out=[]
    for i, ln in enumerate(plan_lines):
        if _is_hito(ln):
            # si no hay acción antes o la anterior también es HITO, inserta acción mínima
            if not out or _is_hito(out[-1]):
                out.append(_minimal_action_for_hito(ln))
        out.append(ln)
    return out

# ---------------- RAG opcional ----------------
try:
    from utils.rag_loader import load_retriever as _load_retriever
except Exception:
    _load_retriever = None

def _rag_ctx_generic(query: str) -> str:
    if not _load_retriever or not os.path.isdir(INDICES_DIR):
        return ""
    try:
        retriever = _load_retriever(INDICES_DIR, emb_model=EMB_MODEL, k=6)
        return retriever(query)
    except Exception:
        return ""

try:
    from utils.helpers_rag_gob import retrieve_gob as _retrieve_gob
except Exception:
    _retrieve_gob = None

def _norm_level_for_rag(s: str) -> str:
    t = (s or "").strip().lower()
    t = (t.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u"))
    if "insuficiente" in t: return "Insuficiente"
    if "básico" in t or "basico" in t: return "Básico"
    if "medio" in t: return "Medio"
    if "avanzado" in t: return "Avanzado"
    return "Básico"

# ---------------- Prompts ----------------

PROMPT_INIT = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Comité PMG. Genera un borrador de acciones concretas y de bajo costo para una OAE chilena pequeña, "
     "EVITANDO diagnóstico/levantamiento. No agregues prefijos como 'Plan de mejora:'. "
     "Usa servicios del Estado de Chile (ClaveÚnica, FEA, Notificación Electrónica, interoperabilidad) SOLO si la brecha/pregunta lo exige. "
     "Todas las tareas deben ser mínimas y abordables por cualquier institución pública (sin plataformas nuevas, sin grandes migraciones ni consultorías extensas; prioriza ajustes simples, reuso y validaciones básicas). "
     "Trabaja SIEMPRE en torno a los HITOS fijados en 'hitos_previos'. "
     "Para CADA HITO, redacta ENTRE 3 y 4 ACCIONES que contribuyan DIRECTAMENTE a lograrlo. "
     "Prohíbe acciones genéricas u ornamentales. "
     "Redacción y formato: sin títulos, sin negritas y sin dos puntos (':'); una acción por línea. "
     "Orden de salida (plan intercalado): para cada HITO N, lista sus acciones y luego escribe 'HITO N: ...'. "
     "El último bloque debe contener una 'acción de cierre' mínima inmediatamente ANTES del último HITO (cierre de brecha)."
     "Si {dimension} contiene “Calidad web”, produce exactamente:"
    "- UN ÚNICO PÁRRAFO de Actividad entre 50 y 90 palabras (sin numeración ni 'Plan de mejora:')."
    "- A continuación, una sola línea iniciada con 'Hito: ' de 12 a 24 palabras, usando exactamente el hito provisto."
    "Prohibido usar títulos o negritas. Lenguaje específico y verificable."),
    ("user",
     "Hitos previos (usar estrictamente):\n{hitos_previos}\n\n"
     "Dimensión: {dimension}\nSubdimensión: {subdimension}\nBrecha: {brecha}\n"
     "Pregunta: {pregunta}\nRespuesta: {respuesta}\nListado previo: {listado}")
])


PROMPT_CONSOLIDAR = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Comité PMG. Trabaja en 2 fases (razona internamente, RESPONDE SOLO JSON):\n"
     "Fase 1 (fijada): Usa EXACTAMENTE los HITOS entregados en 'hitos_previos' "
     "(4 en Procedimiento/Gobernanza, 1 en Calidad web). "
     "Fase 2 (salida): Para CADA HITO, redacta ENTRE 3 y 4 ACCIONES CONCRETAS, MÍNIMAS y de BAJO COSTO que contribuyan DIRECTAMENTE a lograr ese hito.\n"
     "VINCULACIÓN ESTRICTA ACCIÓN↔HITO:\n"
     "- Calidad web y servicios digital: EXACTAMENTE 1 hito; salida en UN ÚNICO PÁRRAFO que comience con “Actividad: …” (50–90 palabras) y termine con “Hito: …” (12–24 palabras) usando el hito provisto; sin numeración ni “Plan de mejora:”."
     " - Para el HITO i, incluye SOLO acciones que contribuyen DIRECTAMENTE a ese HITO; elimina lo ornamental o genérico.\n"
     " - No arrastres acciones entre hitos: cada bloque de acciones termina en su HITO inmediato.\n"
     " - Justo ANTES del HITO final, debe existir una acción de cierre mínima que materialice el logro final.\n"
     "Restricciones generales: tareas mínimas abordables por cualquier OAE (sin plataformas nuevas ni grandes migraciones/consultorías); "
     "servicios del Estado SOLO cuando sean pertinentes; prohibido usar títulos, negritas o ':' en acciones; sin duplicados.\n"
     "Salida obligatoria (JSON con llaves exactas): listado, hitos, plan_intercalado, objetivo, indicador_proceso, indicador_resultado\n"
     "Reglas de formato:\n"
     " - 'hitos' => lista de 'HITO N: ...' (N consecutivo) con los logros definidos en la Fase 1 (mismo orden que 'hitos_previos').\n"
     " - 'listado' => SOLO acciones (sin 'Plan de mejora:' ni 'HITO'), numeradas 1..N y resultantes de concatenar, en orden, las acciones de cada bloque (3–4 por hito).\n"
     " - 'plan_intercalado' => para cada HITO N, lista SUS acciones (3–4) DIRECTAMENTE relacionadas y luego 'HITO N: ...'. "
     "   El último renglón DEBE ser el HITO final (cierre de brecha) precedido por su acción de cierre."),
    ("user",
     "Hitos previos:\n{hitos_previos}\n\n"
     "Plan PMG (borrador/entrada):\n{plan_pmg}\n\n"
     "Intervenciones Abogado:\n{interv_abogado}\n\nImplementador:\n{interv_implementador}\n\nDesarrollador:\n{interv_desarrollador}\n\n"
     "Contexto:\n{dimension} / {subdimension} / {brecha} / {pregunta} / {respuesta}\n\n"
     "Notas:\n{notas}\nRAG:\n{rag}")
])


PROMPT_TITLE = ChatPromptTemplate.from_messages([
    ("system", "Propón un título breve (máx. 12 palabras) para el plan. Sin comillas ni markdown."),
    ("user", "Dimensión: {dimension}\nSubdimensión: {subdimension}\nBrecha: {brecha}\n"
             "Pregunta: {pregunta}\nListado:\n{listado_vigente}")
])

PROMPT_HITO = ChatPromptTemplate.from_messages([
    ("system",
     "Sugiere la lista de HITOS (logros) y su posición 1-indexada. En Gobernanza de datos y Procedimiento administrativo de función específica deben ser EXACTAMENTE 4; en Calidad web y servicios digital EXACTAMENTE 1. "
     "Los hitos deben ser auto-explicativos y describir logros verificables (no evaluaciones), p. ej.: 'queda operativo', 'se publica', 'se dispone de'. "
     "El último hito debe reflejar el cierre/superación de la brecha. "
     "Responde SOLO JSON: [{{\"pos\":1, \"texto\":\"...\"}}, {{\"pos\":4, \"texto\":\"...\"}}]"),
    ("user",
     "Dimensión: {dimension}\nBrecha: {brecha}\nPregunta: {pregunta}\nListado:\n{listado}")
])

# ---------------- API ----------------
class PMGServer:
    
    def __init__(self, grupo_procesos: Optional[str] = None):
        """Inicializa el servidor PMG con tracking opcional.
        
        Args:
            grupo_procesos: ID único para agrupar todas las llamadas LLM de esta ejecución
        """
        self.grupo_procesos = grupo_procesos

    def _rag_for(self, p: Dict[str, Any]) -> str:
        # RAG de gobernanza si aplica; si no, RAG genérico
        try:
            from utils.helpers_rag_gob import retrieve_gob as _retrieve_gob  # import local por seguridad
        except Exception:
            _retrieve_gob = None

        subd = p.get("subdimension", "")
        usar_actual = str(p.get("usar_nivel_rag","")).strip().lower() == "actual"
        nivel_actual_txt = p.get("rag_nivel") or p.get("respuesta") or ""
        nivel_objetivo_txt = p.get("nivel_objetivo") or "Básico"
        nivel_para_rag = _norm_level_for_rag(nivel_actual_txt if usar_actual else nivel_objetivo_txt)

        if _retrieve_gob is not None and subd:
            try:
                if p.get("obligar_hoja_ruta"):
                    return _retrieve_gob(subdimension=subd, nivel_objetivo=nivel_para_rag, k=int(os.getenv("RAG_K","12")))
                dim = (p.get("dimension") or "").lower()
                if "gobernanza" in dim:
                    return _retrieve_gob(subdimension=subd, nivel_objetivo=nivel_para_rag, k=int(os.getenv("RAG_K","12")))
            except Exception:
                pass
        q = f"{p.get('dimension','')} {p.get('subdimension','')} {p.get('brecha','')} {p.get('pregunta','')}"
        return _rag_ctx_generic(q)

    def generate_initial(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un listado inicial de acciones en texto plano.
        - Limpia títulos/negritas/":" en acciones.
        - Aplana listas literales.
        - Garantiza al menos un HITO si el modelo no lo devuelve.
        """
        raw = (PROMPT_INIT | _llm(TEMP_INIT, MAXTOK_INIT, self.grupo_procesos)).invoke(p).content
        lines = _flatten_plan_lines(raw)
        lines = _ensure_one_hito(lines, p.get("pregunta", ""))
        listado = "\n".join(lines).strip()
        return {"status": "ok", "payload": {"listado": listado, "contexto_pm": p.get("contexto_pm", "") or ""}}

    def propose_title(self, p: Dict[str,Any]) -> Dict[str,Any]:
        raw = (PROMPT_TITLE | _llm(TEMP_TITLE, MAXTOK_TITLE, self.grupo_procesos)).invoke(p).content
        return {"status":"ok","payload":{"titulo": raw.strip()}}

    def propose_hito(self, p: Dict[str,Any]) -> Dict[str,Any]:
        raw = (PROMPT_HITO | _llm(TEMP_HITO, MAXTOK_HITO, self.grupo_procesos)).invoke(p).content
        try:
            data = json.loads(raw.strip("`\n "))
        except Exception:
            return {"status":"error","message":"Invalid JSON","raw":raw}
        return {"status":"ok","payload":{"hitos": data}}

    # (conservado por compatibilidad; ya no se usa directamente)
    def _ensure_hitos(self, p: Dict[str,Any], data: Dict[str,Any]) -> List[str]:
        raw_hitos = data.get("hitos") or []
        fixed: List[str] = []
        if isinstance(raw_hitos, list) and any(str(h).strip() for h in raw_hitos):
            n = 1
            for h in raw_hitos:
                s = str(h).strip()
                if isinstance(h, dict):
                    s = str(h.get("texto","")).strip()
                s = re.sub(r"^\s*HITO\s*\d*\s*:\s*", "", s, flags=re.IGNORECASE).strip(": -")
                if s:
                    fixed.append(f"HITO {n}: {s}"); n += 1
        else:
            gen = self.propose_hito({
                "dimension":    p.get("dimension",""),
                "subdimension": p.get("subdimension",""),
                "brecha":       p.get("brecha",""),
                "pregunta":     p.get("pregunta",""),
                "listado":      p.get("plan_pmg","")
            })
            lst = (gen.get("payload") or {}).get("hitos") or []
            n = 1
            for it in lst:
                s = (it.get("texto","") if isinstance(it, dict) else str(it)).strip()
                s = re.sub(r"^\s*HITO\s*\d*\s*:\s*", "", s, flags=re.IGNORECASE).strip(": -")
                if s:
                    fixed.append(f"HITO {n}: {s}"); n += 1

        dim = (p.get("dimension","") or "").lower()
        return _enforce_hito_count_by_dim(dim, fixed, p)

    def consolidate_select(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidación principal:
        - 'Hitos primero' con propose_hito (4 para Proc/Gob; 1 para Calidad Web).
        - Se pasan los 'hitos_previos' al prompt para que las acciones salgan alineadas a ellos.
        - Limpieza de entradas y salidas: aplanado, numeración, fin en HITO, sin título.
        """
        # A) Normaliza plan de entrada
        plan_in_lines = _flatten_plan_lines(p.get("plan_pmg", ""))
        plan_in_lines = _ensure_one_hito(plan_in_lines, p.get("pregunta", ""))
        cleaned_in = "\n".join(plan_in_lines)

        # B) Hitos primero
        pre = self.propose_hito({
            "dimension":    p.get("dimension", ""),
            "subdimension": p.get("subdimension", ""),
            "brecha":       p.get("brecha", ""),
            "pregunta":     p.get("pregunta", ""),
            "listado":      cleaned_in
        })
        pre_hitos = (pre.get("payload") or {}).get("hitos") or []
        dim = p.get("dimension", "") or ""
        norm_pre_hitos = []
        n = 1
        for h in pre_hitos:
            s = (h.get("texto", "") if isinstance(h, dict) else str(h)).strip()
            s = re.sub(r"^\s*HITO\s*\d*\s*:\s*", "", s, flags=re.IGNORECASE).strip(": -")
            if s:
                norm_pre_hitos.append(f"HITO {n}: {s}"); n += 1
        hitos_previos = _enforce_hito_count_by_dim(dim, norm_pre_hitos, p)

        # C) Consolidación con hitos_previos
        rag = p.get("rag") or self._rag_for(p)
        raw = (PROMPT_CONSOLIDAR | _llm(TEMP_CONS, MAXTOK_CONS, self.grupo_procesos)).invoke({
            "hitos_previos": "\n".join(hitos_previos),
            "plan_pmg": cleaned_in,
            "interv_abogado":        p.get("interv_abogado", ""),
            "interv_implementador":  p.get("interv_implementador", ""),
            "interv_desarrollador":  p.get("interv_desarrollador", ""),
            "dimension":    p.get("dimension", ""),
            "subdimension": p.get("subdimension", ""),
            "brecha":       p.get("brecha", ""),
            "pregunta":     p.get("pregunta", ""),
            "respuesta":    p.get("respuesta", ""),
            "notas":        p.get("notas", ""),
            "rag":          rag
        }).content

        # D) Parseo
        try:
            data = json.loads(raw.strip("` \n"))
        except Exception:
            return {"status": "error", "message": "Invalid JSON", "raw": raw}

        # E) Fijar hitos (exactos por dimensión)
        data["hitos"] = _enforce_hito_count_by_dim(dim, data.get("hitos") or hitos_previos or [], p)

        # F) Normalizar plan_intercalado
        pi = data.get("plan_intercalado", "") or ""
        pi_lines = _flatten_plan_lines(pi)
        pi_lines = _clip_extra_hitos_in_plan(pi_lines, dim)
        # Garantizar al menos una acción antes de cada HITO
        pi_lines = _ensure_actions_before_each_hito(pi_lines)
        # Asegurar terminar en HITO
        if pi_lines and not _is_hito(pi_lines[-1]):
            last_h = [x for x in pi_lines if _is_hito(x)]
            if last_h:
                pi_lines.append(last_h[-1])
        elif not pi_lines:
            last = data["hitos"][-1] if data["hitos"] else "HITO 1: Logro alcanzado"
            pi_lines = [last]
        data["plan_intercalado"] = "\n".join(pi_lines)

        # G) Normalizar listado (sin HITO) y numerar
        lst = data.get("listado", [])
        lst_text = "\n".join(lst) if isinstance(lst, list) else str(lst)
        lst_lines = [ln for ln in _flatten_plan_lines(lst_text) if not _is_hito(ln)]
        data["listado"] = [f"{i}.- {ln}" for i, ln in enumerate(lst_lines, 1)]

        # H) Sin título y con saltos de línea consistentes
        data["titulo"] = ""
        data["plan_intercalado"] = _force_newlines(data["plan_intercalado"])

        return {"status": "ok", "payload": data}



