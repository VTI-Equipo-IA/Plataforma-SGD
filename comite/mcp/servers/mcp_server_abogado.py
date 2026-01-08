# mcp_server_abogado.py
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

TEMP_INTERV   = float(os.getenv("ABOGADO_TEMP_INTERV", "0.2"))
TEMP_DECIDE   = float(os.getenv("ABOGADO_TEMP_DECIDE", "0.0"))
TEMP_REVIEW_H = float(os.getenv("ABOGADO_TEMP_REVIEW_H", "0.15"))
TEMP_REVIEW_I = float(os.getenv("ABOGADO_TEMP_REVIEW_I", "0.15"))

MAXTOK_INTERV = int(os.getenv("ABOGADO_MAXTOK_INTERV", "700"))
MAXTOK_DECIDE = int(os.getenv("ABOGADO_MAXTOK_DECIDE", "300"))
MAXTOK_RH     = int(os.getenv("ABOGADO_MAXTOK_RH", "220"))
MAXTOK_RI     = int(os.getenv("ABOGADO_MAXTOK_RI", "220"))

INDICES_DIR   = os.getenv("ABOGADO_INDEX_DIR", "indices/abogado_index")
EMB_MODEL     = os.getenv("ABOGADO_EMB_MODEL", "text-embedding-3-small")

# =========================
# RAG opcional
# =========================
try:
    from utils.rag_loader import load_retriever as _load_retriever
except Exception:
    _load_retriever = None  # sin fallback textual

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
# Pertinencia (llaves amplias, español)
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
        "interoperabilidad", "integración", "api", "servicio web", "registro civil", "intercambio"
    ],
    "atencion_presencial_chileatiende": [
        "presencial", "oficina", "chileatiende", "orientación presencial"
    ],
    "notificaciones_oficiales": [
        "notific", "aviso", "domicilio digital", "correo certificado", "alerta"
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

def _llm(temp: float, max_tokens: Optional[int] = None) -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=temp, max_tokens=max_tokens or None)

# =========================
# Prompts
# =========================
PROMPT_INTERVENTION = ChatPromptTemplate.from_messages([
    ("system",
     "Eres Abogado del Estado de Chile. Evalúas legalidad, cumplimiento normativo y riesgo. "
     "Trabajas con proyectos estatales chilenos y solo sugieres uso de servicios oficiales "
     "(ClaveÚnica, FEA, Tesorería, Registro Civil, ChileAtiende, Domicilio Digital, etc.) "
     "si la brecha/pregunta lo amerita de modo explícito. Evita diagnóstico: se asume hecho. "
     "Formato de respuesta: solo líneas con una de estas formas (sin markdown):\n"
     "- Insertar entre Y e Y+1: <acción concreta y breve>\n"
     "- Eliminar X\n"
     "- Reemplazar X por: <acción>\n"
     "Prioriza bajo costo y reducción de riesgo. Sin títulos ni comentarios adicionales."
     "Permitir sugerir la acción de cierre cuando se traduzca en un acto/regla/documento oficial verificable (bajo costo)"
     "Si una acción no contribuye DIRECTAMENTE al HITO que la sucede, sugiere eliminarla o reemplazarla por una que sí lo haga."),
    ("user",
     "Contexto del plan (PM):\n{contexto_pm}\n\nListado vigente (acciones):\n{listado_vigente}\n\n"
     "Señales RAG (normativa/procedimiento):\n{rag}\n")
])

PROMPT_DECIDE = ChatPromptTemplate.from_messages([
    ("system",
     "Eres Abogado del Estado. Vota sobre la viabilidad legal del plan propuesto.\n"
     "Responde SOLO JSON con claves: {\"vote\": \"approve\"|\"reject\", \"notes\": \"...\"}. "
     "Si detectas riesgo legal alto o incumplimiento normativo, rechaza."),
    ("user",
     "Contexto PM:\n{contexto_pm}\n\nPlan propuesto:\n{plan}\n\nRAG normativo:\n{rag}\n")
])

PROMPT_REVIEW_HITO = ChatPromptTemplate.from_messages([
    ("system",
     "Revisa este HITO desde el punto de vista legal/normativo. "
     "Si está bien redactado y es verificable, devuelve {\"suggestion\":\"OK\"}. "
     "Si requiere ajuste menor, devuelve {\"suggestion\":\"<texto mejorado>\"}. "
     "Solo JSON."),
    ("user",
     "Dimensión: {dimension}\nBrecha: {brecha}\nPregunta: {pregunta}\nHito:\n{hito}\nRAG:\n{rag}\n")
])

# Revisión legal/técnico-normativa de un Indicador de Resultado (1 línea)
# Variables esperadas: contexto_pm, dimension, subdimension, plan_text, indicador_resultado
PROMPT_REVIEW_INDICATOR = ChatPromptTemplate.from_template(
    """Eres el Abogado del Estado de Chile asesorando a un comité PMG.
Revisa y MEJORA un Indicador de Resultado para una iniciativa pública chilena.

Contexto PM (breve):
{contexto_pm}

Dimensión: {dimension}
Subdimensión: {subdimension}

Plan de acciones (resumen):
{plan_text}

Indicador (borrador, puede venir vacío):
{indicador_resultado}

REQUISITOS:
- Devuelve **SOLO UNA LÍNEA** con el Indicador de Resultado final.
- Debe medir un **resultado observable** (no actividades), con **métrica**, **línea base** (si aplica) y **objetivo/variación esperada**; redactado en castellano neutro.
- Ajusta a normativa y práctica del sector público chileno. Evita introducir nuevos sistemas/plataformas; usa insumos disponibles (registros, bitácoras, trámites, sistemas internos).
- No incluyas markdown, viñetas, ni explicaciones. Sin prefijos como "Indicador:".
- Si el borrador está vacío o confunde proceso con resultado, **redáctalo** acorde al plan y a la brecha.

Entrega: la línea final del indicador, sin comillas ni adornos."""
)


PROMPT_ABOGADO_IND_RESULT = ChatPromptTemplate.from_template("""
Eres asesor jurídico del sector público chileno. Ajusta el Indicador de Resultado para:
- Redacción neutral/objetiva (sin adjetivos evaluativos).
- Protección de datos personales (sin identificar personas ni datos sensibles).
- Fuente de verificación razonable y existente (bitácoras/sistemas vigentes).
- Mantenerlo como resultado (no proceso).

Contexto: {contexto_pm}
Dimensión/Subdimensión: {dimension} / {subdimension}
Plan (resumen):
{plan_text}

Indicador propuesto:
{indicador_resultado}

Devuelve SOLO el indicador (una línea).
""".strip())

# =========================
# Helpers de salida
# =========================
def _as_ok(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status":"ok","payload": payload}

def _as_err(msg: str) -> Dict[str, Any]:
    return {"status":"error","message": msg}

# =========================
# API expuesta (nivel módulo)
# =========================
def intervention(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve propuestas con formato:
      - 'Insertar entre Y e Y+1: ...'
      - 'Eliminar X'
      - 'Reemplazar X por: ...'
    Sin comentarios extra. Bajo costo y cumplimiento.
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        lst    = content.get("listado_vigente","")
        rag    = _rag_ctx(f"legalidad cumplimiento normativa: {ctx_pm[:800]} {lst[:800]}")
        raw = (PROMPT_INTERVENTION | _llm(TEMP_INTERV, MAXTOK_INTERV)).invoke({
            "contexto_pm": ctx_pm,
            "listado_vigente": lst,
            "rag": rag
        }).content.strip()

        # Normalización mínima: solo líneas válidas
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        valid = []
        for ln in lines:
            if ln.startswith("Insertar entre Y e Y+1: ") or ln.startswith("Eliminar ") or ln.startswith("Reemplazar "):
                valid.append(ln)
        return _as_ok({"intervencion": "\n".join(valid)})
    except Exception as e:
        # sin fallback textual
        return _as_ok({"intervencion": ""})

def decide(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Voto legal sobre el plan. Responde JSON {"vote":"approve|reject","notes":"..."}.
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        plan   = content.get("plan_propuesto","")
        rag    = _rag_ctx(f"riesgos legales normativa: {ctx_pm[:800]} {plan[:800]}")
        raw = (PROMPT_DECIDE | _llm(TEMP_DECIDE, MAXTOK_DECIDE)).invoke({
            "contexto_pm": ctx_pm,
            "plan": plan,
            "rag": rag
        }).content.strip()
        data = json.loads(raw.strip("` \n"))
        vote = data.get("vote","").strip()
        notes= (data.get("notes","") or "").strip()
        if vote not in ("approve","reject"):
            return _as_ok({"vote":"reject","notes":"Formato de voto inválido"})
        return _as_ok({"vote": vote, "notes": notes})
    except Exception:
        return _as_ok({"vote":"reject","notes": ""})

def review_hito(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Revisión legal de un hito. Devuelve {"suggestion":"OK"} o texto mejorado.
    """
    try:
        rag = _rag_ctx(
            f"{content.get('dimension','')} {content.get('brecha','')} "
            f"{content.get('pregunta','')} {content.get('hito','')}"
        )
        raw = (PROMPT_REVIEW_HITO | _llm(TEMP_REVIEW_H, MAXTOK_RH)).invoke({
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
    Sugerencia de INDICADOR DE RESULTADO (outcome) legalmente apropiado.
    """
    try:
        ctx_pm = content.get("contexto_pm","")
        plan   = content.get("plan","")
        rag    = _rag_ctx(f"indicador resultado legal: {ctx_pm[:800]} {plan[:800]}")
        raw = (PROMPT_REVIEW_INDICATOR | _llm(TEMP_REVIEW_I, MAXTOK_RI)).invoke({
            "contexto_pm": ctx_pm,
            "plan": plan,
            "rag": rag
        }).content.strip()
        # Respuesta debe ser una sola línea sin markdown
        text = re.sub(r"\s+", " ", raw).strip(" .")
        return _as_ok({"suggestion": text})
    except Exception:
        return _as_ok({"suggestion": ""})
    
def review_result_indicator(content: dict) -> dict:
    raw = (PROMPT_ABOGADO_IND_RESULT | _llm(0.1, 350)).invoke({
        "contexto_pm": content.get("contexto_pm",""),
        "dimension": content.get("dimension",""),
        "subdimension": content.get("subdimension",""),
        "plan_text": content.get("plan_text",""),
        "indicador_resultado": content.get("indicador_resultado",""),
    }).content
    return _as_ok({"suggestion": strip_code_fences(raw).strip()})

# Registro opcional (si otro cliente lo requiere)
_TOOL_MAP = {
    "intervention": intervention,
    "decide": decide,
    "review_hito": review_hito,
    "review_indicator": review_indicator,
    "review_result_indicator": review_result_indicator,

}








