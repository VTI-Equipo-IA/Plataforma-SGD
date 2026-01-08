# mcp_server_implementador.py
from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# =========================
# Configuración
# =========================
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TEMP_INTERV = float(os.getenv("IMPL_TEMP_INTERV", "0.25"))
TEMP_DECIDE = float(os.getenv("IMPL_TEMP_DECIDE", "0.0"))

MAXTOK_INTERV = int(os.getenv("IMPL_MAXTOK_INTERV", "700"))
MAXTOK_DECIDE = int(os.getenv("IMPL_MAXTOK_DECIDE", "300"))

INDICES_DIR   = os.getenv("IMPL_INDEX_DIR", "indices/implementador_index")
EMB_MODEL     = os.getenv("IMPL_EMB_MODEL", "text-embedding-3-small")

# =========================
# RAG opcional
# =========================
try:
    from utils.rag_loader import load_retriever as _load_retriever
except Exception:
    _load_retriever = None

FENCE_OPEN = re.compile(r"^\s*```(?:json)?\s*", flags=re.IGNORECASE)
FENCE_CLOSE = re.compile(r"\s*```\s*$", flags=re.IGNORECASE)

def strip_code_fences(text: str) -> str:
    if not isinstance(text, str):
        return text
    t = text.strip()
    if t.startswith("```"):
        t = FENCE_OPEN.sub("", t, count=1)
        t = FENCE_CLOSE.sub("", t)
        return t.strip()
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", t, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return t

def _rag_ctx(query: str) -> str:
    if not _load_retriever:
        return ""
    if not os.path.isdir(INDICES_DIR):
        return ""
    try:
        retriever = _load_retriever(INDICES_DIR, emb_model=EMB_MODEL, k=6)
        return retriever(query)
    except Exception:
        return ""

# =========================
# Pertinencia
# =========================
_NEED_KEYS: Dict[str, List[str]] = {
    "autenticacion_oficial": ["autentic", "clave única", "claveunica", "login"],
    "firma_electronica": ["firma", "validez", "jurídic", "legal", "fea", "firma electrónica"],
    "pagos_tesoreria": ["pago", "tesorería", "arancel", "boleta", "tasas"],
    "interoperabilidad": ["interoperabilidad", "integración", "api", "servicio web", "registro civil"],
    "atencion_presencial_chileatiende": ["presencial", "oficina", "chileatiende"],
    "notificaciones_oficiales": ["notific", "domicilio digital", "aviso", "correo certificado"],
}

def _necesita(feature: str, texto: str) -> bool:
    return any(k in (texto or "").lower() for k in _NEED_KEYS.get(feature, []))

def _texto_pertinencia(ctx: Dict[str, Any], rag: str) -> str:
    return f"{ctx.get('contexto_pm','')} {ctx.get('listado_vigente','')} {rag}"

# =========================
# Helpers
# =========================
def _llm(temp: float, max_tokens: Optional[int] = None) -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=temp, max_tokens=max_tokens or None)

def _as_ok(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status":"ok","payload": payload}

def _as_err(msg: str) -> Dict[str, Any]:
    return {"status":"error","message": msg}

# =========================
# Prompts
# =========================
PROMPT_INTERVENTION = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Implementador del Estado de Chile. Evalúas factibilidad operativa y presupuesto. "
     "Tu rol es ser RESTRICTIVO: debes priorizar ELIMINAR acciones innecesarias, luego SIMPLIFICAR/REUSAR, "
     "y solo como última opción sugerir AGREGAR nuevas tareas. "
     "Usa servicios oficiales solo si la brecha lo amerita. "
     "Formato ESTRICTO por línea:\n"
     "- Eliminar X\n"
     "- Reemplazar X por: <acción>\n"
     "- Insertar entre Y e Y+1: <acción>\n"
     "No devuelvas comentarios, títulos ni diagnósticos. Sin markdown."
     "enfatiza la prioridad por eliminar/simplificar y exigir una acción de cierre mínima si falta"
     "Si una acción no contribuye DIRECTAMENTE al HITO que la sucede, sugiere eliminarla o reemplazarla por una que sí lo haga."),
    ("user",
     "Contexto PM:\n{contexto_pm}\nListado vigente:\n{listado_vigente}\nRAG:\n{rag}\n")
])

PROMPT_DECIDE = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Implementador del Estado. Vota sobre la factibilidad operativa y presupuestaria del plan. "
     "Responde SOLO JSON: {\"vote\": \"approve\"|\"reject\", \"notes\": \"...\"}. "
     "Si excede recursos básicos de un servicio público pequeño, rechaza."),
    ("user",
     "Contexto:\n{contexto_pm}\nPlan:\n{plan}\nRAG:\n{rag}\n")
])

# Revisión de HITO (implementación / operación / presupuesto)
PROMPT_REVIEW_HITO = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Implementador del Estado de Chile. Revisa un HITO desde factibilidad operativa y presupuesto.\n"
     "Si el hito es claro, alcanzable con recursos limitados y verificable, devuelve JSON: {\"suggestion\":\"OK\"}.\n"
     "Si requiere un ajuste menor para hacerlo ejecutable a bajo costo, devuelve JSON: {\"suggestion\":\"<texto mejorado>\"}.\n"
     "No uses markdown ni comentarios adicionales."),
    ("user",
     "Dimensión: {dimension}\nBrecha: {brecha}\nPregunta: {pregunta}\nHito:\n{hito}\nRAG:\n{rag}\n")
])

# Revisión/Sugerencia de INDICADOR DE RESULTADO (desde implementación: realista, medible, bajo costo)
PROMPT_REVIEW_INDICATOR = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Implementador del Estado de Chile. Propón o ajusta un INDICADOR DE RESULTADO en **UNA LÍNEA**:\n"
     "- Debe medir un **resultado** observable (no actividades) vinculado al plan.\n"
     "- Usar **fuentes existentes** (bitácoras, sistemas, registros internos) y **periodicidad realista**.\n"
     "- Redacción neutral, sin prefijos ni markdown. Bajo presupuesto, sin plataformas nuevas."),
    ("user",
     "Contexto PM (breve):\n{contexto_pm}\n\nPlan (resumen):\n{plan}\n\nRAG:\n{rag}\n")
])


PROMPT_IMPL_IND_RESULT = ChatPromptTemplate.from_template("""
Eres implementador público con foco en **bajo presupuesto**. Ajusta el Indicador de Resultado para que:
- Se mida con datos y fuentes **ya disponibles** (o ajustes mínimos).
- Evite requerir plataformas nuevas o consultorías.
- Mantenga umbral/periodo realista para instituciones pequeñas.
- Siga siendo resultado (no proceso).

Contexto: {contexto_pm}
Dimensión/Subdimensión: {dimension} / {subdimension}
Plan (resumen):
{plan_text}

Indicador propuesto:
{indicador_resultado}

Devuelve SOLO el indicador ajustado (una línea).
""".strip())

# =========================
# API expuesta
# =========================
def intervention(content: Dict[str, Any]) -> Dict[str, Any]:
    try:
        ctx_pm = content.get("contexto_pm","")
        lst    = content.get("listado_vigente","")
        rag    = _rag_ctx(f"factibilidad costos: {ctx_pm[:800]} {lst[:800]}")
        raw = (PROMPT_INTERVENTION | _llm(TEMP_INTERV, MAXTOK_INTERV)).invoke({
            "contexto_pm": ctx_pm,
            "listado_vigente": lst,
            "rag": rag
        }).content.strip()

        # Filtrado estricto
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        valid = []
        for ln in lines:
            if ln.startswith("Eliminar ") or ln.startswith("Reemplazar ") or ln.startswith("Insertar entre Y e Y+1: "):
                valid.append(ln)
        return _as_ok({"intervencion": "\n".join(valid)})
    except Exception:
        return _as_ok({"intervencion": ""})

def decide(content: Dict[str, Any]) -> Dict[str, Any]:
    try:
        ctx_pm = content.get("contexto_pm","")
        plan   = content.get("plan_propuesto","")
        rag    = _rag_ctx(f"factibilidad costos: {ctx_pm[:800]} {plan[:800]}")
        raw = (PROMPT_DECIDE | _llm(TEMP_DECIDE, MAXTOK_DECIDE)).invoke({
            "contexto_pm": ctx_pm,
            "plan": plan,
            "rag": rag
        }).content.strip()
        data = json.loads(raw.strip("` \n"))
        vote = data.get("vote","").strip()
        notes= (data.get("notes","") or "").strip()
        if vote not in ("approve","reject"):
            return _as_ok({"vote":"reject","notes":"Formato inválido"})
        return _as_ok({"vote": vote, "notes": notes})
    except Exception:
        return _as_ok({"vote":"reject","notes": ""})

def review_hito(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Revisión operativa/presupuestaria de un HITO.
    Devuelve {'suggestion':'OK'} o un texto mejorado (JSON en el prompt).
    """
    try:
        rag = _rag_ctx(
            f"{content.get('dimension','')} {content.get('brecha','')} "
            f"{content.get('pregunta','')} {content.get('hito','')}"
        )
        raw = (PROMPT_REVIEW_HITO | _llm(0.15, 220)).invoke({
            "dimension": content.get("dimension",""),
            "brecha": content.get("brecha",""),
            "pregunta": content.get("pregunta",""),
            "hito": content.get("hito",""),
            "rag": rag
        }).content.strip()
        data = json.loads(raw.strip("` \n"))
        return _as_ok({"suggestion": (data.get("suggestion","") or "").strip()})
    except Exception:
        return _as_ok({"suggestion": ""})

def review_indicator(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sugerencia/Ajuste de INDICADOR DE RESULTADO desde mirada de implementación (una sola línea).
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        plan   = content.get("plan","")
        rag    = _rag_ctx(f"indicador resultado implementacion bajo costo: {ctx_pm[:800]} {plan[:800]}")
        raw = (PROMPT_REVIEW_INDICATOR | _llm(0.15, 220)).invoke({
            "contexto_pm": ctx_pm,
            "plan": plan,
            "rag": rag
        }).content.strip()
        text = re.sub(r"\s+", " ", raw).strip(" .")
        return _as_ok({"suggestion": text})
    except Exception:
        return _as_ok({"suggestion": ""})

    
def review_result_indicator(content: dict) -> dict:
    raw = (PROMPT_IMPL_IND_RESULT | _llm(0.1, 320)).invoke({
        "contexto_pm": content.get("contexto_pm",""),
        "dimension": content.get("dimension",""),
        "subdimension": content.get("subdimension",""),
        "plan_text": content.get("plan_text",""),
        "indicador_resultado": content.get("indicador_resultado",""),
    }).content
    return _as_ok({"suggestion": strip_code_fences(raw).strip()})

# Registro opcional
_TOOL_MAP = {
    "intervention": intervention,
    "decide": decide,
    "review_hito": review_hito,
    "review_indicator": review_indicator,
    "review_result_indicator": review_result_indicator,
}
