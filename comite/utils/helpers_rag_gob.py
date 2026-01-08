# utils/helpers_rag_gob.py
from __future__ import annotations
import os, re
from typing import List, Tuple
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Mapeo flexible de nombres de nivel (para regex robusto)
NIV_MAP = {
    "Insuficiente": ["insuficiente"],
    "Básico": ["básico", "basico"],
    "Medio": ["medio"],
    "Avanzado": ["avanzado"],
}

def _emb_model() -> str:
    return os.getenv("PMG_EMB_MODEL", "text-embedding-3-small")

def _index_path() -> str:
    # índice dedicado a la Hoja de Ruta MGDE (recomendado)
    return os.getenv("RAG_INDEX_GOBERNANZA", "indices/hoja_ruta_index")

def load_vs_gob():
    idx = _index_path()
    emb = OpenAIEmbeddings(model=_emb_model())
    return FAISS.load_local(idx, emb, allow_dangerous_deserialization=True)

def _lvl_regex(target: str) -> re.Pattern:
    toks = NIV_MAP.get(target, [target.lower()])
    pat = r"(?i)\b(" + "|".join(map(re.escape, toks)) + r")\b"
    return re.compile(pat)

def retrieve_gob(subdimension: str, nivel_objetivo: str, k: int = 12) -> str:
    """
    Recupera SOLO pasajes que mencionen la subdimensión y el nivel objetivo.
    Si nada calza, relaja a solo subdimensión.
    """
    vs = load_vs_gob()
    query = f"Subdimensión: {subdimension}. Nivel: {nivel_objetivo}. Lista de tareas/actividades por nivel del MGDE."
    docs_scores = vs.similarity_search_with_score(query, k=k)
    rgx_lvl = _lvl_regex(nivel_objetivo)
    sub_norm = (subdimension or "").strip().lower()

    # 1) filtro estricto: subdimensión + nivel
    sel: List[Tuple[str, float]] = []
    for d, sc in docs_scores:
        txt = d.page_content or ""
        if sub_norm and sub_norm not in txt.lower():
            continue
        if not rgx_lvl.search(txt):
            continue
        sel.append((txt, sc))

    # 2) relax si quedó vacío
    if not sel and sub_norm:
        for d, sc in docs_scores:
            txt = d.page_content or ""
            if sub_norm in txt.lower():
                sel.append((txt, sc))

    sel.sort(key=lambda t: t[1])
    partes: List[str] = [txt.strip() for (txt, _) in sel[:k]]
    return "\n\n".join(partes)
