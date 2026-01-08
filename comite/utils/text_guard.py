# utils/text_guard.py
# -*- coding: utf-8 -*-
import re

# Patrones: cargos/roles, fechas explícitas, plazos, montos, aprobaciones formales, nombres propios “sospechosos”
ROLE_WORDS = r"(director(?:a)?|jefe(?:a)?|gerent[ea]|subdirector(?:a)?|encargad[oa]|ministro|seremi|alcalde|intendente|contralor|rector|decano)"
DATE_PATTERNS = r"(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b|\b20\d{2}\b)"
DEADLINE_WORDS = r"(antes del|a más tardar|plazo|fecha límite|deadline)"
MONEY = r"(\$\s?\d+([\.,]\d+)*|\b\d+(\.\d{3})*(,\d+)?\s*(CLP|USD|EUR)\b|\bpresupuesto\b|\bcosto[s]?\b)"
APPROVALS = r"(documento oficial|resoluci[oó]n|decreto|firma|aprobaci[oó]n|oficio|memor[aá]ndum)"
CONTACT = r"(\bmailto:|\bhttps?://|\bwww\.)"

ROLE_RE = re.compile(ROLE_WORDS, re.IGNORECASE)
DATE_RE = re.compile(DATE_PATTERNS, re.IGNORECASE)
DEADLINE_RE = re.compile(DEADLINE_WORDS, re.IGNORECASE)
MONEY_RE = re.compile(MONEY, re.IGNORECASE)
APPROVALS_RE = re.compile(APPROVALS, re.IGNORECASE)
CONTACT_RE = re.compile(CONTACT, re.IGNORECASE)

def sanitize_line(s: str) -> str:
    """Elimina menciones prohibidas y reescribe suavemente indicaciones que impliquen autoridad/fecha/monto/aprobación."""
    if not s: 
        return s

    # Quitar URLs/correos
    s = CONTACT_RE.sub("", s)

    # Eliminar plazos/fechas explícitas y frases de deadline
    s = DEADLINE_RE.sub("", s)
    s = DATE_RE.sub("", s)

    # Eliminar cargos/roles explícitos
    s = ROLE_RE.sub("", s)

    # Eliminar montos/presupuesto
    s = MONEY_RE.sub("", s)

    # Quitar menciones de aprobación formal
    s = APPROVALS_RE.sub("documentar y difundir internamente", s)

    # Limpiezas de doble espacios / puntuación
    s = re.sub(r"\s{2,}", " ", s).strip(" .;-")
    return s.strip()

def sanitize_block(text: str) -> str:
    """Aplica sanitize_line línea por línea; preserva numeración si existe."""
    if not text:
        return text
    lines = text.splitlines()
    out = []
    for ln in lines:
        # conservar numeración inicial "1. ", "2) " si existe
        m = re.match(r"^\s*(\d+[\.\)]\s*)(.*)$", ln)
        if m:
            prefix, body = m.groups()
            clean = sanitize_line(body)
            if clean:
                out.append(f"{prefix}{clean}")
        else:
            clean = sanitize_line(ln)
            if clean:
                out.append(clean)
    return "\n".join(out)
