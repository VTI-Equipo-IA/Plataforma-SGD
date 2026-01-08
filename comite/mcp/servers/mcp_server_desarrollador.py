# mcp_server_desarrollador.py
from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")

# =========================
# Configuración
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TEMP_INTERV = float(os.getenv("DEV_TEMP_INTERV", "0.25"))
TEMP_DECIDE = float(os.getenv("DEV_TEMP_DECIDE", "0.0"))
TEMP_RH     = float(os.getenv("DEV_TEMP_REVIEW_H", "0.15"))
TEMP_RI     = float(os.getenv("DEV_TEMP_REVIEW_I", "0.15"))

MAXTOK_INTERV = int(os.getenv("DEV_MAXTOK_INTERV", "700"))
MAXTOK_DECIDE = int(os.getenv("DEV_MAXTOK_DECIDE", "300"))
MAXTOK_RH     = int(os.getenv("DEV_MAXTOK_RH", "220"))
MAXTOK_RI     = int(os.getenv("DEV_MAXTOK_RI", "220"))

INDICES_DIR   = os.getenv("DEV_INDEX_DIR", "indices/desarrollador_index")
EMB_MODEL     = os.getenv("DEV_EMB_MODEL", "text-embedding-3-small")

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
# Pertinencia (llaves amplias en español)
# =========================
_NEED_KEYS: Dict[str, List[str]] = {
    "autenticacion_oficial": [
        "autentic", "identidad", "clave única", "claveunica", "login", "ingreso seguro"
    ],
    "firma_electronica": [
        "firma", "validez", "jurídic", "legal", "documento firmado", "fe avanzada", "firma electrónica"
    ],
    "pagos_tesoreria": [
        "pago", "tasas", "arancel", "boleta", "recaudación", "tesorería"
    ],
    "interoperabilidad": [
        "interoperabilidad", "integración", "api", "servicio web", "plataforma externa", "registro civil"
    ],
    "atencion_presencial_chileatiende": [
        "presencial", "oficina", "chileatiende", "orientación presencial"
    ],
    "notificaciones_oficiales": [
        "notific", "aviso", "correo certificado", "domicilio digital", "alerta"
    ],
    "identidad_legal": [
        "rut", "run", "verificar identidad", "cédula", "datos personales", "padrón"
    ],
    "remision_documental": [
        "remisión", "derivación", "remitir", "adjuntar", "folio", "expediente"
    ],
    "gestion_expediente": [
        "expediente", "carpeta", "historial", "trazabilidad", "resolución", "oficio", "dictamen"
    ],
    "publicacion_transparencia": [
        "transparencia", "publicar", "difusión", "norma", "instructivo", "web institucional"
    ],
}

def _necesita(feature: str, texto: str) -> bool:
    t = (texto or "").lower()
    return any(k in t for k in _NEED_KEYS.get(feature, []))

def _texto_pertinencia(ctx: Dict[str, Any], rag: str) -> str:
    base = " ".join([
        ctx.get("contexto_pm",""),
        ctx.get("listado_vigente",""),
    ]).strip()
    return f"{base} {rag}".strip()

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
     "Eres el Desarrollador del Estado de Chile. Evalúas viabilidad técnica, mantención y costo de oportunidad. "
     "Principios: MINIMALISMO TÉCNICO, REUSO, BAJO COSTO, mejoras incrementales (accesibilidad básica, performance simple, "
     "registros mínimos, validaciones simples). No impongas stacks nuevos ni grandes migraciones salvo que la brecha lo exija. "
     "Solo sugiere servicios oficiales (ClaveÚnica, FEA, Tesorería, Registro Civil, ChileAtiende, Domicilio Digital, etc.) "
     "si la brecha/pregunta lo amerita según contexto. Evita diagnóstico: ya se hizo.\n"
     "Formato ESTRICTO por línea (sin markdown, sin títulos):\n"
     "- Eliminar X\n"
     "- Reemplazar X por: <acción concreta y breve>\n"
     "- Insertar entre Y e Y+1: <acción concreta y breve>\n"
     "Prioriza eliminar/simplificar/reusar antes que agregar."
     "Si el listado no contiene una acción mínima que materialice el cierre de la brecha," 
     "sugiere Insertar entre Y e Y+1: <acción de cierre mínima> inmediatamente antes del HITO final."
     "Si una acción no contribuye DIRECTAMENTE al HITO que la sucede, sugiere eliminarla o reemplazarla por una que sí lo haga."),
    ("user",
     "Contexto PM:\n{contexto_pm}\nListado vigente (acciones):\n{listado_vigente}\nRAG técnico:\n{rag}\n")
])

PROMPT_DECIDE = ChatPromptTemplate.from_messages([
    ("system",
     "Eres Desarrollador del Estado. Vota sobre viabilidad técnica simple, mantención y costo de oportunidad. "
     "Responde SOLO JSON: {\"vote\": \"approve\"|\"reject\", \"notes\": \"...\"}. "
     "Rechaza si requiere stack nuevo complejo, integraciones costosas o mantenimiento alto para una OAE pequeña."),
    ("user",
     "Contexto PM:\n{contexto_pm}\nPlan propuesto:\n{plan}\nRAG técnico:\n{rag}\n")
])

PROMPT_REVIEW_HITO = ChatPromptTemplate.from_messages([
    ("system",
     "Revisa un HITO desde el punto de vista técnico. Si es claro, alcanzable y verificable con esfuerzos modestos, "
     "devuelve {\"suggestion\":\"OK\"}. Si requiere mejora menor (p. ej., precisión técnica mínima), "
     "devuelve {\"suggestion\":\"<texto mejorado>\"}. Solo JSON."),
    ("user",
     "Dimensión: {dimension}\nBrecha: {brecha}\nPregunta: {pregunta}\nHito:\n{hito}\nRAG técnico:\n{rag}\n")
])

PROMPT_REVIEW_INDICATOR = ChatPromptTemplate.from_messages([
    ("system",
     "Eres desarrollador de datos en una OAE chilena. Propón un INDICADOR DE RESULTADO en UNA LÍNEA:\n"
     "- Debe medir un resultado observable (no actividades).\n"
     "- Menciona (si aplica) métrica, línea base y objetivo/variación.\n"
     "- Señala una fuente de verificación existente (bitácora/sistema/dataset institucional) y periodicidad razonable.\n"
     "- Bajo costo y realista para instituciones pequeñas. Sin markdown, sin prefijos, sin explicaciones."),
    ("user",
     "Contexto PM (breve):\n{contexto_pm}\n\nPlan de acciones (resumen):\n{plan}\n\nRAG técnico:\n{rag}\n")
])

PROMPT_DEV_IND_RESULT = ChatPromptTemplate.from_template("""
Eres desarrollador de datos en una OAE chilena. Ajusta el Indicador de Resultado para:
- Incluir fuente concreta y existente (bitácora/sistema/dataset institucional).
- Señalar periodicidad de medición (mensual/trimestral/anual) acorde al plan.
- Mantenerlo como resultado (no actividad).

Contexto: {contexto_pm}
Dimensión/Subdimensión: {dimension} / {subdimension}
Plan (resumen):
{plan_text}

Indicador propuesto:
{indicador_resultado}

Devuelve SOLO el indicador final (una línea).
""".strip())

# =========================
# API expuesta
# =========================
def intervention(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce propuestas ESTRICTAS:
      - 'Eliminar X'
      - 'Reemplazar X por: ...'
      - 'Insertar entre Y e Y+1: ...'
    con sesgo a reuso/simplificación y bajo costo.
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        lst    = content.get("listado_vigente","")
        rag    = _rag_ctx(f"viabilidad tecnica minimalismo reuso: {ctx_pm[:800]} {lst[:800]}")
        raw = (PROMPT_INTERVENTION | _llm(TEMP_INTERV, MAXTOK_INTERV)).invoke({
            "contexto_pm": ctx_pm,
            "listado_vigente": lst,
            "rag": rag
        }).content.strip()

        # Filtrado estricto de formato
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        valid = []
        for ln in lines:
            if (
                ln.startswith("Eliminar ")
                or ln.startswith("Reemplazar ")
                or ln.startswith("Insertar entre Y e Y+1: ")
            ):
                valid.append(ln)
        return _as_ok({"intervencion": "\n".join(valid)})
    except Exception:
        return _as_ok({"intervencion": ""})

def decide(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Voto técnico sobre el plan. JSON {'vote':'approve|reject','notes':'...'}.
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        plan   = content.get("plan_propuesto","")
        rag    = _rag_ctx(f"riesgo tecnico mantenibilidad costo oportunidad: {ctx_pm[:800]} {plan[:800]}")
        raw = (PROMPT_DECIDE | _llm(TEMP_DECIDE, MAXTOK_DECIDE)).invoke({
            "contexto_pm": ctx_pm,
            "plan": plan,
            "rag": rag
        }).content.strip()
        data = json.loads(raw.strip("` \n"))
        vote = (data.get("vote","") or "").strip()
        notes= (data.get("notes","") or "").strip()
        if vote not in ("approve","reject"):
            return _as_ok({"vote":"reject","notes":"Formato inválido"})
        return _as_ok({"vote": vote, "notes": notes})
    except Exception:
        return _as_ok({"vote":"reject","notes": ""})

def review_hito(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Revisión técnica de un hito. Devuelve {'suggestion':'OK'} o texto mejorado.
    """
    try:
        rag = _rag_ctx(
            f"{content.get('dimension','')} {content.get('brecha','')} "
            f"{content.get('pregunta','')} {content.get('hito','')}"
        )
        raw = (PROMPT_REVIEW_HITO | _llm(TEMP_RH, MAXTOK_RH)).invoke({
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
    Sugerencia de indicador de resultado desde mirada técnica (una frase, verificable).
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        plan   = content.get("plan","")
        rag    = _rag_ctx(f"indicador resultado tecnico: {ctx_pm[:800]} {plan[:800]}")
        raw = (PROMPT_REVIEW_INDICATOR | _llm(TEMP_RI, MAXTOK_RI)).invoke({
            "contexto_pm": ctx_pm,
            "plan": plan,
            "rag": rag
        }).content.strip()
        text = re.sub(r"\s+", " ", raw).strip(" .")
        return _as_ok({"suggestion": text})
    except Exception:
        return _as_ok({"suggestion": ""})
    
def review_result_indicator(content: dict) -> dict:
    raw = (PROMPT_DEV_IND_RESULT | _llm(0.1, 320)).invoke({
        "contexto_pm": content.get("contexto_pm",""),
        "dimension": content.get("dimension",""),
        "subdimension": content.get("subdimension",""),
        "plan_text": content.get("plan_text",""),
        "indicador_resultado": content.get("indicador_resultado",""),
    }).content
    return _as_ok({"suggestion": strip_code_fences(raw).strip()})


# Registro opcional (si algún cliente lo requiere)
_TOOL_MAP = {
    "intervention": intervention,
    "decide": decide,
    "review_hito": review_hito,
    "review_indicator": review_indicator,  # <-- con comillas
    "review_result_indicator": review_result_indicator,
}
