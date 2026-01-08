# utils/roadmap_loader.py
from __future__ import annotations
import json, os, unicodedata, re
from typing import Dict, List, Tuple

def _norm(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def load_roadmap_json(path: str) -> Dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe JSON de hoja de ruta: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_obligatory_activities(
    data: Dict,
    dimension_key: str,         # "Gobernanza de datos"
    subdimension_name: str,     # del Excel
    target_level: str           # "básico" | "medio" | "avanzado" (nivel a alcanzar)
) -> List[str]:
    """
    Retorna SOLO actividades (sin nombres de criterios) para el par (subdimensión, nivel).
    Incluye las de 'all_levels' y las específicas del nivel.
    """
    dim_map = data.get(dimension_key, {})
    # normalizamos claves de subdimensión a un dict paralelo
    subd_map = {}
    for k, v in dim_map.items():
        subd_map[_norm(k)] = v

    subd_norm = _norm(subdimension_name)
    if subd_norm not in subd_map:
        return []

    node = subd_map[subd_norm]
    acts: List[str] = []

    # 1) comunes a todos los niveles
    for a in node.get("all_levels", []) or []:
        if a and a.strip():
            acts.append(a.strip())

    # 2) específicas del nivel
    level_norm = _norm(target_level)
    if level_norm not in ("basico","medio","avanzado","básico"):
        # admite variantes (por si viene “Básico” con tilde, o “Insuficiente”→ transición a Básico)
        if "insuficiente" in level_norm:
            level_norm = "basico"
        elif "básico" in level_norm:
            level_norm = "basico"

    for k_level, node_lvl in node.items():
        if k_level in ("all_levels",): 
            continue
        if _norm(k_level) != level_norm: 
            continue
        criterios = (node_lvl or {}).get("criterios", {}) or {}
        for _, items in criterios.items():
            for a in items or []:
                if a and a.strip():
                    acts.append(a.strip())

    # de-dup manteniendo orden
    seen = set(); out=[]
    for a in acts:
        key = _norm(a)
        if key not in seen:
            seen.add(key); out.append(a)
    return out
