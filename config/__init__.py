# config/__init__.py
"""
Módulo de configuración de la aplicación Flask.
Contiene utilidades para cargar settings, seguridad y variables de entorno.
"""

from .settings import load_config
from .security import encrypt_value, decrypt_value  # si implementas cifrado Fernet más adelante

__all__ = ["load_config", "encrypt_value", "decrypt_value"]
