# comite/utils/tracked_llm_mcp.py
"""
Wrapper para usar tracking de tokens en los servidores MCP del comité.
Version simplificada que funciona con las estructuras existentes de los servidores.
"""
import os
import sys
from typing import Optional
from langchain_openai import ChatOpenAI

# Agregar el directorio raíz al path para importar services
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from services.tracked_llm import TrackedChatOpenAI


def create_mcp_llm(
    model: str,
    temperature: float,
    app_name: str = "PMG",
    max_tokens: Optional[int] = None,
    grupo_procesos: Optional[str] = None,
    track_enabled: bool = True
) -> ChatOpenAI:
    """
    Crea un LLM con tracking para uso en servidores MCP.
    
    Args:
        model: Nombre del modelo (e.g., "gpt-4o-mini")
        temperature: Temperatura del modelo
        app_name: Nombre de la aplicación/agente (e.g., "comite-pmg")
        max_tokens: Máximo de tokens (opcional)
        grupo_procesos: ID para agrupar llamadas de un mismo proceso
        track_enabled: Si False, usa ChatOpenAI estándar sin tracking
        
    Returns:
        TrackedChatOpenAI o ChatOpenAI según track_enabled
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    
    if not track_enabled:
        # Modo sin tracking (útil para desarrollo/testing)
        kwargs = {
            'model': model,
            'temperature': temperature,
            'api_key': api_key
        }
        if max_tokens:
            kwargs['max_tokens'] = max_tokens
        return ChatOpenAI(**kwargs)
    
    # Modo con tracking
    kwargs = {
        'model': model,
        'temperature': temperature,
        'api_key': api_key,
        'app_name': app_name,
        'grupo_procesos': grupo_procesos,
        'track_enabled': True
    }
    if max_tokens:
        kwargs['max_tokens'] = max_tokens
    
    return TrackedChatOpenAI(**kwargs)


# Alias para compatibilidad con código existente
def _llm(
    temp: float,
    max_tokens: Optional[int] = None,
    app_name: str = "PMG",
    grupo_procesos: Optional[str] = None,
    model: Optional[str] = None
) -> ChatOpenAI:
    """
    Función helper compatible con la firma existente _llm() en los servidores MCP.
    
    Uso en servidores MCP:
        # Antes:
        llm = _llm(temp=0.2, max_tokens=500)
        
        # Ahora (con tracking):
        llm = _llm(temp=0.2, max_tokens=500, app_name="comite-pmg", grupo_procesos=proceso_id)
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    return create_mcp_llm(
        model=model,
        temperature=temp,
        app_name=app_name,
        max_tokens=max_tokens,
        grupo_procesos=grupo_procesos,
        track_enabled=True
    )
