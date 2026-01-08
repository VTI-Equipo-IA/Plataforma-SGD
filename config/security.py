# config/security.py
"""
Utilidades de seguridad:
- Cifrado/descifrado con Fernet (clave desde FERNET_SECRET).
- Enmascarado de secretos para UI/logs.
- Comparación constante (evita timing attacks).
- Generación de claves Fernet (utilidad offline).

Requisitos: cryptography
    pip install cryptography
"""

from __future__ import annotations
import os
import base64
from functools import lru_cache
from typing import Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception as e:
    # Permite importar el módulo sin cryptography instalada,
    # pero al usar funciones de cifrado se lanzará un error claro.
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


class SecurityConfigError(RuntimeError):
    """Se lanza cuando falta FERNET_SECRET o la librería cryptography."""


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """
    Retorna una instancia Fernet usando FERNET_SECRET del entorno.
    Acepta:
      - Clave Fernet válida (urlsafe base64 de 32 bytes)
      - Clave cruda de 32 bytes en base64 a la que le falte padding

    No genera la clave automáticamente para evitar claves débiles por accidente.
    """
    if Fernet is None:
        raise SecurityConfigError(
            "La librería 'cryptography' no está instalada. "
            "Instala con: pip install cryptography"
        )

    secret = os.environ.get("FERNET_SECRET")
    if not secret:
        raise SecurityConfigError(
            "FERNET_SECRET no está definida en el entorno. "
            "Genera una con generate_fernet_key() y colócala en .env"
        )

    # Normaliza: permitir claves sin padding o raw base64
    try:
        # Si ya es una clave Fernet válida, esto no fallará
        Fernet(secret)
        return Fernet(secret)
    except Exception:
        pass

    # Intento de normalización: agregar padding si falta
    try:
        # Agregar padding '=' si la longitud no es múltiplo de 4
        pad_len = (-len(secret)) % 4
        normalized = secret + ("=" * pad_len)
        # Validar que decode funcione
        base64.urlsafe_b64decode(normalized.encode("utf-8"))
        return Fernet(normalized.encode("utf-8"))
    except Exception as e:
        raise SecurityConfigError(
            "FERNET_SECRET inválida. Debe ser una clave urlsafe base64 generada por Fernet."
        ) from e


def encrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Cifra un string y retorna un token urlsafe base64 (str).
    Retorna None si value es None o cadena vacía (normaliza a None).
    """
    if value is None:
        return None
    value = str(value)
    if value == "":
        return None
    f = _get_fernet()
    token: bytes = f.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(token: Optional[str]) -> Optional[str]:
    """
    Descifra un token Fernet (str) y retorna el valor original (str).
    Retorna None si token es None o vacío.
    Lanza SecurityConfigError si el token es inválido/corrupto.
    """
    if token is None:
        return None
    token = token.strip()
    if token == "":
        return None
    f = _get_fernet()
    try:
        plain: bytes = f.decrypt(token.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken as e:
        raise SecurityConfigError("Token Fernet inválido o corrupto.") from e


def mask_secret(value: Optional[str], show: int = 4) -> str:
    """
    Enmascara un secreto para UI/logs (no mostrar en claro).
    Ej.: 'sk_live_ABCDEF' -> '**********CDEF' (últimos 4 visibles).
    """
    if not value:
        return ""
    s = str(value)
    if len(s) <= show:
        return "*" * len(s)
    return "*" * (len(s) - show) + s[-show:]


def constant_time_compare(a: Optional[str], b: Optional[str]) -> bool:
    """
    Comparación en tiempo constante para secretos (evita timing attacks).
    """
    if a is None or b is None:
        return False
    # Implementación simple evitando early return
    if len(a) != len(b):
        # Aún así recorre para que el tiempo no delate diferencias de longitud
        result = 0
        la, lb = len(a), len(b)
        for i in range(max(la, lb)):
            ca = ord(a[i]) if i < la else 0
            cb = ord(b[i]) if i < lb else 0
            result |= (ca ^ cb)
        return result == 0
    result = 0
    for x, y in zip(a, b):
        result |= (ord(x) ^ ord(y))
    return result == 0


def generate_fernet_key() -> str:
    """
    Utilidad para generar una clave Fernet segura (urlsafe base64).
    Úsala offline y pega el resultado en tu .env como FERNET_SECRET.

    Ejemplo:
        python -c "from config.security import generate_fernet_key; print(generate_fernet_key())"
    """
    if Fernet is None:
        raise SecurityConfigError("Instala 'cryptography' para generar una clave Fernet.")
    return Fernet.generate_key().decode("utf-8")


__all__ = [
    "encrypt_value",
    "decrypt_value",
    "mask_secret",
    "constant_time_compare",
    "generate_fernet_key",
    "SecurityConfigError",
]
