# services/external_ai_bridge.py
"""
Este archivo NO implementa el modelo. Solo define el contrato
para llamar a tu servicio de IA ya existente.
"""
from typing import Dict

class AIError(RuntimeError):
    pass

def generate_plan(dim_slug: str, row_data: Dict, target: str, config: Dict | None = None) -> str:
    """
    Llama a TU servicio de IA y retorna un texto numerado (8–10 pasos).
    - dim_slug: 'gobernanza-datos', etc.
    - row_data: dict con campos de la fila (e.g., 'Brecha', 'Dimension', 'Subdimension'/'Subdimensión', ...)
    - target: 'diego' | 'luis' → campo donde guardar el plan
    - config: parámetros opcionales (proveedor, modelo, temperature, etc.)
    """
    # TODO: Implementar la llamada a tus modelos ya existentes.
    # Aquí solo va el puente, sin claves ni dependencias reales.
    # Si falla, lanza AIError con un mensaje claro.
    raise AIError("Servicio de IA no configurado. Implementa la llamada en external_ai_bridge.generate_plan.")
