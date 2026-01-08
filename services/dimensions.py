# services/dimensions.py
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class DimensionDef:
    slug: str
    label: str
    table_name: str
    dimension_filter: str  # Valor de referencia principal del campo "Dimension"
    match_strings: List[str]  # Cadenas alternativas para hacer match en la BD (ilike)
    hidden_columns: List[str]  # Columnas a ocultar en el listado para esta dimensión

# Todas las dimensiones usan la misma tabla ptd_planes, pero filtran por el campo "Dimension"
DIMENSIONS = [
    DimensionDef(
        slug="gobernanza-datos", 
        label="Gobernanza de datos", 
        table_name="ptd_planes",
        dimension_filter="Gobernanza de datos",
        match_strings=[
            "Gobernanza de datos",
            "Gobernanza de Datos",
        ],
        hidden_columns=[
            "n_pregunta", "pregunta",  # minúsculas
            "N_Pregunta", "Pregunta",  # variantes
        ],
    ),
    DimensionDef(
        slug="calidad-web-servicios-digital", 
        label="Calidad web y servicios digital", 
        table_name="ptd_planes",
        dimension_filter="Calidad web y servicios digitales",
        match_strings=[
            "Calidad web y servicios digital",
            "Calidad web y servicios digitales",
        ],
        hidden_columns=[
            "nivel_de_madurez", "Nivel_de_madurez",
        ],
    ),
    DimensionDef(
        slug="procedimiento-administrativo", 
        label="Procedimiento administrativo", 
        table_name="ptd_planes",
        dimension_filter="Procedimiento administrativo de función específica",
        match_strings=[
            "Procedimiento administrativo",
            "Procedimiento administrativo de función específica",
        ],
        hidden_columns=[
            "nivel_de_madurez", "Nivel_de_madurez",
            "n_pregunta", "N_Pregunta",
        ],
    ),
]

def get_dimension(slug: str) -> DimensionDef | None:
    return next((d for d in DIMENSIONS if d.slug == slug), None)

def default_dimension() -> DimensionDef:
    return DIMENSIONS[0]

def all_dimensions() -> list[DimensionDef]:
    return DIMENSIONS
