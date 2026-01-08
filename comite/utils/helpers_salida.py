# ===== helpers_salida.py =====
import os, re, json
from typing import Tuple
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# ----- LLM determinista para micro-título -----
PROMPT_TITLE_FROM_LIST = ChatPromptTemplate.from_messages([
    ("system",
     "Genera un TÍTULO breve y descriptivo (máx. 12 palabras) para el siguiente contenido. "
     "No uses comillas, markdown ni numeraciones."),
    ("user", "Contenido:\n{contenido}")
])

def _llm_zero():
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    return ChatOpenAI(model=model, temperature=0.0)

# ----- Limpieza y normalización de texto -----
_MD_HDR = re.compile(r"^#{1,6}\s*", flags=re.MULTILINE)
_MD_BOLD = re.compile(r"\*\*|__|`+")
_MD_BULLET = re.compile(r"^[>\-\*]\s*", flags=re.MULTILINE)
_ENUM_LEAD = re.compile(r"^\s*\d+\s*[\.\-\)]\s*")

def _clean_md(s: str) -> str:
    if not s: return ""
    s = _MD_HDR.sub("", s)
    s = _MD_BOLD.sub("", s)
    s = _MD_BULLET.sub("", s)
    return s.strip()

# ----- Filtro: eliminar diagnóstico/levantamiento -----
_DIAG_PAT = re.compile(r"\b(diagn(o|ó)stic|levantamiento)\b", flags=re.IGNORECASE)

def _remove_diagnostics(lines):
    out = []
    for ln in lines:
        if _DIAG_PAT.search(ln or ""):
            continue
        out.append(ln)
    return out

# ----- Reenumeración 1.-, 2.-, ... -----
def _renumber(lines, max_items=20):
    clean = []
    for ln in lines:
        t = _ENUM_LEAD.sub("", ln or "").strip(" .;-")
        if t:
            clean.append(t)
    out = []
    for i, t in enumerate(clean[:max_items], 1):
        out.append(f"{i}.- {t}")
    return out

# ----- Asegurar título (si falta, pedirlo al LLM a partir de contenido) -----
def _ensure_title(titulo: str, contenido: str) -> str:
    t = (titulo or "").strip()
    if t:
        return _clean_md(t)
    # Generar con LLM determinista
    raw = (PROMPT_TITLE_FROM_LIST | _llm_zero()).invoke({"contenido": contenido}).content.strip()
    return _clean_md(raw)

# ===== API principal =====
def build_cell_text(
    titulo: str,
    cuerpo: str,
    modo: str = "lista"   # "lista" (procedimiento/gobernanza) o "parrafo" (calidad web)
) -> Tuple[str, str]:
    """
    Retorna (texto_para_celda, titulo_puro)
    - texto_para_celda: 'Título\\r\\n\\r\\n<listado o párrafo>' con CRLF para Excel
    - titulo_puro: solo el título limpio (por si guardas en columna independiente)
    """
    cuerpo = _clean_md(cuerpo or "")

    if modo == "lista":
        # separar por líneas y limpiar
        lines = [ln.strip() for ln in cuerpo.splitlines() if ln.strip()]
        # quitar diagnósticos
        lines = _remove_diagnostics(lines)
        # si quedó vacío, deja una acción mínima
        if not lines:
            lines = ["Ajustes incrementales con servicios estatales existentes (sin diagnóstico)."]
        # reenumerar
        listado = "\n".join(_renumber(lines))
        titulo_final = _ensure_title(titulo, listado)
        texto = f"{titulo_final}\r\n\r\n{listado}"
        return texto, titulo_final

    else:  # "parrafo" (Calidad web)
        # quitar diagnósticos
        if _DIAG_PAT.search(cuerpo):
            cuerpo = _DIAG_PAT.sub("", cuerpo).strip()
        if not cuerpo:
            cuerpo = "Acción mínima para pasar de 'No' a 'Sí' reusando servicios estatales existentes."
        titulo_final = _ensure_title(titulo, cuerpo)
        texto = f"{titulo_final}\r\n\r\n{cuerpo}"
        return texto, titulo_final
