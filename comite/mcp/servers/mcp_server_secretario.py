# mcp_server_secretario.py
from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")

# =========================
# Configuración
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TEMP_AGG   = float(os.getenv("SEC_TEMP_AGG", "0.15"))
TEMP_HITO  = float(os.getenv("SEC_TEMP_HITO", "0.15"))
TEMP_INDI  = float(os.getenv("SEC_TEMP_INDI", "0.15"))
TEMP_PARA  = float(os.getenv("SEC_TEMP_PARA", "0.15"))

MAXTOK_AGG  = int(os.getenv("SEC_MAXTOK_AGG", "450"))
MAXTOK_HITO = int(os.getenv("SEC_MAXTOK_HITO", "280"))
MAXTOK_INDI = int(os.getenv("SEC_MAXTOK_INDI", "280"))
MAXTOK_PARA = int(os.getenv("SEC_MAXTOK_PARA", "300"))

INDICES_DIR = os.getenv("SEC_INDEX_DIR", "indices/secretario_index")
EMB_MODEL   = os.getenv("SEC_EMB_MODEL", "text-embedding-3-small")

# =========================
# RAG opcional
# =========================
try:
    from utils.rag_loader import load_retriever as _load_retriever
except Exception:
    _load_retriever = None  # si no está, seguimos sin contexto extra

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
# Helpers
# =========================
def _llm(temp: float, max_tokens: Optional[int] = None) -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=temp, max_tokens=max_tokens or None)

def _as_ok(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status":"ok","payload": payload}

def _strip_once(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().strip(" .")

def _lines(s: str) -> list[str]:
    return [ln.strip() for ln in (s or "").splitlines() if ln.strip()]

# =========================
# Prompts
# =========================
PROMPT_AGG = ChatPromptTemplate.from_messages([
    ("system",
    "Eres el Secretario del Comité PMG. Resume y ordena las propuestas de Abogado, Implementador y Desarrollador. "
    "Devuelve un RESUMEN CONCISO en texto plano (sin markdown), conservando el formato de acciones en infinitivo, "
    "bajo costo y sin duplicados. "
    "Descarta explícitamente las acciones que no contribuyan DIRECTAMENTE al HITO que las sucede."),
    ("user",
     "Intervención Abogado:\n{abogado}\n\nIntervención Implementador:\n{implementador}\n\n"
     "Intervención Desarrollador:\n{desarrollador}\n\nContexto RAG:\n{rag}\n")
])

PROMPT_FINALIZE_HITO = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Secretario. Devuelve el texto FINAL de un HITO del plan, en UNA ORACIÓN, "
     "como logro verificable y auto-explicativo (p. ej., 'queda operativo', 'se publica', 'se dispone de'). "
     "Evita evaluaciones/juicios ('revisar', 'evaluar', 'diagnosticar'). "
     "Reglas:\n"
     "- Si las tres sugerencias son 'OK' o están vacías, conserva el hito.\n"
     "- Si alguna sugiere cambios menores, integra los ajustes.\n"
     "- Si corresponde al hito de cierre, redacta el logro de manera que deje explícita la superación de la brecha/pregunta.\n"
     "- Sin markdown, sin comillas, sin diagnósticos."),
    ("user",
     "Hito base:\n{hito}\n\nSugerencia Abogado: {abogado}\nSugerencia Implementador: {implementador}\n"
     "Sugerencia Desarrollador: {desarrollador}\n\nContexto RAG:\n{rag}\n")
])


PROMPT_FINALIZE_INDICATOR = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Secretario. Devuelve un INDICADOR DE RESULTADO (outcome) en UNA FRASE, "
     "medible, claro, sin diagnósticos, que valide el cumplimiento del plan. "
     "Combina la propuesta base (si existe) con sugerencias de Abogado/Implementador/Desarrollador. "
     "Sin markdown, sin comillas."),
    ("user",
     "Indicador base (si existe):\n{indicador_base}\n\n"
     "Sugerencia Abogado: {abogado}\nSugerencia Implementador: {implementador}\nSugerencia Desarrollador: {desarrollador}\n\n"
     "Contexto PM:\n{contexto_pm}\nTítulo del plan: {titulo}\nRAG:\n{rag}\n")
])

PROMPT_FINALIZE_PARAGRAPH = ChatPromptTemplate.from_messages([
    ("system",
     "Eres el Secretario. Fusiona las tres posturas en un solo PÁRRAFO breve (3–4 líneas máx.), "
     "coherente, en texto plano, sin bullets ni markdown."),
    ("user",
      "Abogado:\n{abogado}\n\nImplementador:\n{implementador}\n\nDesarrollador:\n{desarrollador}\n\nRAG:\n{rag}\n")
])

PROMPT_SEC_FINAL_IND = ChatPromptTemplate.from_template("""
Eres secretario del comité. Consolida el **Indicador de Resultado** final a partir del borrador PMG y las tres revisiones.
Prioriza: legalidad (abogado), bajo costo/realismo (implementador), medibilidad/fuente/periodicidad (desarrollador).
Devuelve SOLO una línea final, sin prefijos.

Borrador PMG: {borrador}
Abogado: {abogado}
Implementador: {implementador}
Desarrollador: {desarrollador}
""".strip())

# =========================
# API expuesta
# =========================
def aggregate(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sintetiza intervenciones en un resumen conciso (sin duplicados).
    """
    try:
        abogado       = content.get("abogado","")
        implementador = content.get("implementador","")
        desarrollador = content.get("desarrollador","")
        rag = _rag_ctx(f"{abogado[:400]} {implementador[:400]} {desarrollador[:400]}")

        raw = (PROMPT_AGG | _llm(TEMP_AGG, MAXTOK_AGG)).invoke({
            "abogado": abogado,
            "implementador": implementador,
            "desarrollador": desarrollador,
            "rag": rag
        }).content.strip()

        resumen = _strip_once(raw)
        return _as_ok({"resumen": resumen})
    except Exception:
        return _as_ok({"resumen": ""})

def finalize_hito(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consensa un HITO final a partir de 'hito' y sugerencias 'abogado', 'implementador', 'desarrollador'.
    """
    try:
        hito = content.get("hito","")
        abo  = content.get("abogado","")
        imp  = content.get("implementador","")
        dev  = content.get("desarrollador","")
        rag  = _rag_ctx(f"{hito} {abo} {imp} {dev}")

        raw = (PROMPT_FINALIZE_HITO | _llm(TEMP_HITO, MAXTOK_HITO)).invoke({
            "hito": hito, "abogado": abo, "implementador": imp, "desarrollador": dev, "rag": rag
        }).content.strip()

        h_final = _strip_once(raw)
        return _as_ok({"hito": h_final})
    except Exception:
        return _as_ok({"hito": ""})

def finalize_result_indicator(payload: dict) -> dict:
    raw = (PROMPT_SEC_FINAL_IND | _llm(0.1, 220)).invoke({
        "borrador": payload.get("borrador",""),
        "abogado": payload.get("abogado",""),
        "implementador": payload.get("implementador",""),
        "desarrollador": payload.get("desarrollador",""),
    }).content
    return _as_ok({"indicador_resultado": strip_code_fences(raw).strip()})

def finalize_paragraph(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parrafo único a partir de las tres posturas (se usa como fallback en algunos mains).
    """
    try:
        abo  = content.get("abogado","")
        imp  = content.get("implementador","")
        dev  = content.get("desarrollador","")
        rag  = _rag_ctx(f"{abo} {imp} {dev}")

        raw = (PROMPT_FINALIZE_PARAGRAPH | _llm(TEMP_PARA, MAXTOK_PARA)).invoke({
            "abogado": abo, "implementador": imp, "desarrollador": dev, "rag": rag
        }).content.strip()

        par = _strip_once(raw)
        if par and not par.endswith("."):
            par += "."
        return _as_ok({"parrafo": par})
    except Exception:
        return _as_ok({"parrafo": ""})

# Registro opcional
_TOOL_MAP = {
    "aggregate": aggregate,
    "finalize_hito": finalize_hito,
    "finalize_result_indicator": finalize_result_indicator,
    "finalize_paragraph": finalize_paragraph,
}

if __name__ == "__main__":
    # smoke test mínimo
    demo = aggregate({
        "abogado": "Eliminar X\nInsertar entre Y e Y+1: Actualizar reglamento.",
        "implementador": "Reemplazar X por: Simplificar formulario.",
        "desarrollador": "Insertar entre Y e Y+1: Agregar validación HTML mínima."
    })
    print(json.dumps(demo, ensure_ascii=False, indent=2))