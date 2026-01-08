# utils/topic_contract.py
# -*- coding: utf-8 -*-
import re
from typing import Tuple, List

_STOP = {"de","la","el","los","las","y","o","en","del","para","con","por",
         "un","una","al","se","que","es","son","a","su","sus","lo","como"}

def topic_key(dimension: str, subdimension: str, pregunta: str, max_words: int = 20) -> str:
    """
    1 línea (≤ ~180 chars) que capture el foco temático de la pregunta.
    Heurística simple por keywords sin LLM.
    """
    base = f"{dimension} · {subdimension} · {pregunta}".lower()
    toks = re.findall(r"\b[\wáéíóúñ]{3,}\b", base)
    toks = [t for t in toks if t not in _STOP]
    s = " ".join(toks[:max_words]).strip()
    return s[:180] if s else (pregunta or dimension or "tema actual")[:180]

def topic_scope_exclusions(dimension: str) -> str:
    """
    Reglas negativas cortas según dimensión actual.
    """
    d = (dimension or "").lower()
    if "calidad web" in d:
        return "No tratar gobernanza de datos ni procedimientos administrativos."
    if "gobernanza de datos" in d:
        return "No tratar calidad web ni procedimientos administrativos."
    if "procedimiento administrativo" in d:
        return "No tratar calidad web ni gobernanza de datos."
    return "No mezclar con temas ajenos a la dimensión actual."

def extract_keywords(text: str, k: int = 10) -> List[str]:
    toks = re.findall(r"\b[\wáéíóúñ]{4,}\b", (text or "").lower())
    seen=set(); out=[]
    for t in toks:
        if t in _STOP: 
            continue
        if t not in seen:
            seen.add(t); out.append(t)
        if len(out) >= k:
            break
    return out
