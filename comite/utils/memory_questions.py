# utils/memory_questions.py
# -*- coding: utf-8 -*-
import os, json, hashlib, unicodedata, re
from typing import List, Dict, Optional

MEM_PATH = os.environ.get("QUEST_MEM_PATH", ".memory/preguntas.jsonl")
MAX_KEPT  = int(os.environ.get("QUEST_MEM_MAX", "500"))  # guarda hasta 500

def _ensure_dir(path: str):
    d = os.path.dirname(path) or "."
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _norm(s: Optional[str]) -> str:
    return (s or "").strip()

_WS_RX = re.compile(r"\s+")
_PUNC_RX = re.compile(r"[^\w\s]")  # quita signos (conserva letras/dígitos/_ y espacios)

def _canonicalize(text: str) -> str:
    """
    Canon para comparación:
    - minúsculas
    - quita tildes
    - colapsa espacios
    - remueve signos de puntuación
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # quita tildes
    s = s.lower()
    s = _PUNC_RX.sub(" ", s)
    s = _WS_RX.sub(" ", s).strip()
    return s

def _make_key(dimension: str, subdimension: str, instrumento: str, indicador: str, pregunta: str) -> str:
    """
    La identidad usa campos relevantes + pregunta canónica.
    """
    parts = [
        _canonicalize(dimension),
        _canonicalize(subdimension),
        _canonicalize(instrumento),
        _canonicalize(indicador),
        _canonicalize(pregunta),
    ]
    base = " | ".join(parts)
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]

def load_all() -> List[Dict]:
    if not os.path.exists(MEM_PATH):
        return []
    out=[]
    with open(MEM_PATH, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln: 
                continue
            try:
                out.append(json.loads(ln))
            except:
                pass
    return out

def _write_all(rows: List[Dict]) -> None:
    _ensure_dir(MEM_PATH)
    with open(MEM_PATH, "w", encoding="utf-8") as f:
        for r in rows[-MAX_KEPT:]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def add_question(dimension: str, subdimension: str, instrumento: str, indicador: str,
                 brecha: str, iniciativa: str, pregunta: str) -> Dict:
    """
    Agrega (o devuelve) el registro canónico de la pregunta actual.
    Si ya existe (misma canónica + mismos campos clave), reusa el ID.
    """
    key = _make_key(dimension, subdimension, instrumento, indicador, pregunta)
    rec = {
        "id": key,
        "dimension": _norm(dimension),
        "subdimension": _norm(subdimension),
        "instrumento": _norm(instrumento),
        "indicador": _norm(indicador),
        "brecha": _norm(brecha),
        "iniciativa": _norm(iniciativa),
        "pregunta": _norm(pregunta),
        "pregunta_canon": _canonicalize(pregunta),
    }
    rows = load_all()
    if any(r.get("id")==key for r in rows):
        # ya existe; nada que escribir
        return rec
    rows.append(rec)
    if len(rows) > MAX_KEPT:
        rows = rows[-MAX_KEPT:]
    _write_all(rows)
    return rec

def other_questions(current_id: str, limit: int = 50) -> List[str]:
    """
    Devuelve SOLO los enunciados de otras preguntas, excluyendo el current_id.
    """
    if not current_id:
        return []
    out=[]
    for r in load_all():
        if r.get("id") != current_id:
            q = r.get("pregunta","")
            if q:
                out.append(q)
                if len(out) >= limit:
                    break
    return out
