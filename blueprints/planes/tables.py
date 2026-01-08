# blueprints/planes/tables.py
"""
Helpers de tabla para /planes:
- Cálculo de columnas visibles (respetando el esquema real de cada tabla).
- Saneamiento de parámetros de orden.
- Utilidades de paginación y truncado seguro para celdas.
- Detección de columnas de 'plan' (Nombre_Actividad_Hito_*).

Uso típico desde routes.py:
    from .tables import (
        compute_visible_columns, sanitize_order_params,
        paginate_meta, is_plan_column, trunc
    )

    visible_cols = compute_visible_columns(table)
    order, direction = sanitize_order_params(table, order, direction)
    meta = paginate_meta(total, page, per_page)
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any

# Columnas sugeridas para priorizar en el listado si existen en la tabla
PREFERRED_ORDER = [
    # Campos de contexto prioritarios (excluyendo id/fechas por defecto)
    "Dimension", "Subdimension", "Instrumento",
    "Indicador", "Brecha", "Nivel_de_madurez",
    "N_Pregunta", "Pregunta", 
    "Iniciativa", "Objetivo_Iniciativa",
    "Autor", "Indicador_Proceso", "Indicador_Resultado",
    "N_Actividad_Hito", "Tipo", "Descripcion",
]

PLAN_COLUMNS_CANDIDATES = [
    "Descripcion",
    "Objetivo_Iniciativa",
]

SEARCHABLE_CANDIDATES = [
    "Brecha", "Indicador", "Pregunta", "Iniciativa",
    "Descripcion", "Subdimension", "Instrumento",
    "Objetivo_Iniciativa", "Indicador_Proceso", "Indicador_Resultado"
]


def compute_visible_columns(table, exclude: List[str] | None = None, limit: int | None = None) -> List[str]:
    """
    Devuelve una lista de columnas visibles para la tabla:
    - Excluye 'id' por defecto y cualquier nombre en `exclude`.
    - Ordena priorizando PREFERRED_ORDER y luego el resto.
    - `limit` permite recortar la cantidad de columnas (opcional).
    """
    exclude = set(exclude or [])
    # Excluir por defecto columnas técnicas
    default_exclude = {
        "id",
        "fecha_creacion", "fecha_actualizacion",
        # Posibles variantes
        "Fecha_Creacion", "Fecha_Actualizacion",
        "created_at", "updated_at",
        # Ocultar la columna de dimensión (es redundante con la pestaña/selector)
        "Dimension", "dimension",
    }
    exclude.update(default_exclude)

    # Normalizar exclusiones a case-insensitive según columnas reales de la tabla
    exclude_lower = {e.lower() for e in exclude}
    all_cols_real = list(table.c.keys())
    # Construye el conjunto final de exclusiones mapeando por nombre real
    effective_exclude = set()
    for c in all_cols_real:
        if c in exclude or c.lower() in exclude_lower:
            effective_exclude.add(c)

    all_cols = [c for c in all_cols_real if c not in effective_exclude]

    # Prioriza por PREFERRED_ORDER
    preferred = [c for c in PREFERRED_ORDER if c in all_cols]
    rest = [c for c in all_cols if c not in preferred]
    cols = preferred + rest

    if limit and limit > 0:
        cols = cols[:limit]
    return cols


def sanitize_order_params(table, order: str | None, direction: str | None) -> Tuple[str | None, str]:
    """
    Normaliza parámetros de orden:
    - Si `order` no es columna válida, vuelve None.
    - `direction` solo 'asc' o 'desc'; por defecto 'asc'.
    """
    valid_dir = "desc" if (direction or "").lower() == "desc" else "asc"
    if order and order in table.c:
        return order, valid_dir
    return None, valid_dir


def paginate_meta(total: int, page: int, per_page: int) -> Dict[str, int]:
    """
    Calcula metadatos de paginación para la plantilla.
    """
    total_pages = (total // per_page) + (1 if total % per_page else 0)
    page = max(1, min(page, max(1, total_pages)))
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "offset": (page - 1) * per_page,
    }


def is_plan_column(col_name: str) -> bool:
    """
    True si la columna corresponde a un campo de plan (Nombre_Actividad_Hito_*).
    """
    return col_name in PLAN_COLUMNS_CANDIDATES


def plan_targets_available(table) -> List[str]:
    """
    Retorna los targets de plan disponibles en la tabla actual.
    Ej.: ['diego', 'luis'] si existen ambas columnas.
    """
    targets = []
    if "Nombre_Actividad_Hito_Diego" in table.c:
        targets.append("diego")
    if "Nombre_Actividad_Hito_Luis" in table.c:
        targets.append("luis")
    return targets


def trunc(value: Any, limit: int = 240) -> str:
    """
    Trunca strings largos para celdas. Respeta None y no-strings.
    """
    if value is None:
        return ""
    s = str(value)
    return s if len(s) <= limit else s[:limit] + "…"


def existing_searchable_columns(table) -> List[str]:
    """
    Retorna la lista de columnas buscables que existen en la tabla actual.
    Útil para construir UI de búsqueda avanzada o tooltips.
    """
    return [c for c in SEARCHABLE_CANDIDATES if c in table.c]


def normalize_direction(direction: str | None) -> str:
    """
    Normaliza a 'asc' o 'desc' (por si lo necesitas en plantillas).
    """
    return "desc" if (direction or "").lower() == "desc" else "asc"


# ------------------------
# Presentación de columnas
# ------------------------
SPECIAL_LABELS: Dict[str, str] = {
    # Estándar
    "Dimension": "Dimensión",
    "dimension": "Dimensión",
    "Subdimension": "Subdimensión",
    "Descripcion": "Descripción",

    # Fechas
    "fecha_creacion": "Fecha de creación",
    "fecha_actualizacion": "Fecha de actualización",
    "Fecha_Creacion": "Fecha de creación",
    "Fecha_Actualizacion": "Fecha de actualización",

    # Indicadores / objetivos
    "Objetivo_Iniciativa": "Objetivo de Iniciativa",
    "Indicador_Proceso": "Indicador de Proceso",
    "Indicador_Resultado": "Indicador de Resultado",

    # Números / niveles
    "N_Pregunta": "N° Pregunta",
    "n_pregunta": "N° Pregunta",
    "N_Actividad_Hito": "N° Actividad/Hito",
    "Nivel_de_madurez": "Nivel de madurez",
    "nivel_de_madurez": "Nivel de madurez",

    # Campos IA / plan
    "Nombre_Actividad_Hito_Diego": "Nombre Actividad/Hito (Diego)",
    "Nombre_Actividad_Hito_Luis": "Nombre Actividad/Hito (Luis)",
}

LOWER_WORDS = {"de", "del", "la", "las", "los", "y", "o", "en", "para"}


def pretty_label(col_name: str) -> str:
    """Devuelve una etiqueta legible para encabezados de tabla.
    - Aplica mapeos especiales (acentos y formatos específicos).
    - Convierte snake_case a palabras separadas.
    - Ajusta preposiciones a minúsculas.
    """
    if not col_name:
        return ""

    # 1) Mapeos específicos primero
    if col_name in SPECIAL_LABELS:
        return SPECIAL_LABELS[col_name]

    # 2) Generación genérica: snake_case -> palabras
    raw = col_name.replace("_", " ")

    # Si es CamelCase sin guiones bajos, inserta espacios simples (opcional simple)
    # Ej.: "NombreActividad" -> "NombreActividad" (dejamos así si no hay guiones)

    # Title-case y luego baja preposiciones
    parts = raw.split()
    titled = [p.capitalize() for p in parts]
    for i, p in enumerate(titled):
        if p.lower() in LOWER_WORDS and i != 0:
            titled[i] = p.lower()
    label = " ".join(titled)

    # 3) Correcciones comunes de acentos por heurística ligera
    label = label.replace("Subdimension", "Subdimensión")
    label = label.replace("Descripcion", "Descripción")

    return label
