# services/tracked_llm.py
"""
Wrappers y utilidades para usar LLMs con tracking automático de consumo.
"""
import os
from typing import Optional, Any, Dict
from langchain_openai import ChatOpenAI
try:
    # LangChain v0.x
    from langchain.schema import BaseMessage  # type: ignore
except ModuleNotFoundError:
    # LangChain v1.x
    from langchain_core.messages import BaseMessage  # type: ignore
from langchain_core.runnables import RunnableLambda
from .token_tracker import get_tracker, extract_usage_from_response


class TrackedChatOpenAI(ChatOpenAI):
    """
    Subclase de ChatOpenAI que automáticamente registra el consumo de tokens.
    Usa campos privados para evitar conflictos con Pydantic.
    
    Uso:
        llm = TrackedChatOpenAI(
            model="gpt-4o",
            app_name="plataforma-sgd",
            grupo_procesos="generacion_plan_123"
        )
        response = llm.invoke("Tu prompt aquí")
        # El consumo se registra automáticamente
        
        # Compatible con chains:
        chain = prompt | llm
        response = chain.invoke({"input": "..."})
    """
    
    def __init__(
        self,
        app_name: str = "PMG",
        grupo_procesos: Optional[str] = None,
        track_enabled: bool = True,
        **kwargs
    ):
        """
        Args:
            app_name: Nombre de la aplicación para el tracking
            grupo_procesos: Identificador para agrupar múltiples llamadas
            track_enabled: Si False, deshabilita el tracking (útil para debug)
            **kwargs: Argumentos para ChatOpenAI (model, temperature, etc.)
        """
        # Primero inicializar la clase base
        super().__init__(**kwargs)
        
        # Luego agregar atributos de tracking usando object.__setattr__ para evitar Pydantic
        object.__setattr__(self, '_app_name', app_name)
        object.__setattr__(self, '_grupo_procesos', grupo_procesos)
        object.__setattr__(self, '_track_enabled', track_enabled)
        object.__setattr__(self, '_tracker', get_tracker() if track_enabled else None)
    
    def invoke(self, input, config=None, **kwargs):
        """Override de invoke para registrar consumo."""
        track_enabled = object.__getattribute__(self, '_track_enabled')
        
        if not track_enabled:
            return super().invoke(input, config=config, **kwargs)
        
        tracker = object.__getattribute__(self, '_tracker')
        app_name = object.__getattribute__(self, '_app_name')
        grupo_procesos = object.__getattribute__(self, '_grupo_procesos')
        
        with tracker.track_execution(
            app=app_name,
            proveedor="OpenAI",
            version_modelo=self.model_name,
            grupo_procesos=grupo_procesos
        ) as track_info:
            try:
                response = super().invoke(input, config=config, **kwargs)
                
                # Extraer tokens de la respuesta
                usage = extract_usage_from_response(response)
                track_info['tokens_entrada'] = usage['tokens_entrada']
                track_info['tokens_salida'] = usage['tokens_salida']
                track_info['tokens_cache'] = usage.get('tokens_cache')
                track_info['status'] = 'Exito'
                
                return response
                
            except Exception as e:
                track_info['status'] = 'Fallo'
                raise
    
    def set_grupo_procesos(self, grupo_procesos: str):
        """Actualiza el grupo_procesos para las siguientes llamadas."""
        object.__setattr__(self, '_grupo_procesos', grupo_procesos)


def create_tracked_llm(
    model: Optional[str] = None,
    temperature: float = 0.3,
    app_name: str = "PMG",
    grupo_procesos: Optional[str] = None,
    max_tokens: Optional[int] = None,
    track_enabled: bool = True,
    **kwargs
) -> TrackedChatOpenAI:
    """
    Factory function para crear un LLM con tracking.
    
    Args:
        model: Nombre del modelo (por defecto usa OPENAI_MODEL del .env)
        temperature: Temperatura del modelo
        app_name: Nombre de la aplicación
        grupo_procesos: ID para agrupar llamadas relacionadas
        max_tokens: Máximo de tokens en la respuesta
        track_enabled: Si False, deshabilita el tracking
        **kwargs: Otros parámetros para ChatOpenAI
        
    Returns:
        TrackedChatOpenAI configurado
        
    Ejemplo:
        llm = create_tracked_llm(
            model="gpt-4o",
            temperature=0.2,
            app_name="agente-maestro-gd",
            grupo_procesos="plan_gd_20250116_001"
        )
        response = llm.invoke("Genera un plan...")
    """
    if model is None:
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY no encontrada en .env")
    
    llm_kwargs = {
        'model': model,
        'temperature': temperature,
        'api_key': api_key,
        'app_name': app_name,
        'grupo_procesos': grupo_procesos,
        'track_enabled': track_enabled,
        **kwargs
    }
    
    if max_tokens:
        llm_kwargs['max_tokens'] = max_tokens
    
    return TrackedChatOpenAI(**llm_kwargs)


def track_manual_call(
    tokens_entrada: Optional[int],
    tokens_salida: Optional[int],
    tiempo_ejecucion_ms: int,
    app_name: str,
    modelo: str = "gpt-4o",
    proveedor: str = "OpenAI",
    grupo_procesos: Optional[str] = None,
    status: str = "Exito",
    tokens_cache: Optional[int] = None,
) -> bool:
    """
    Función para registrar manualmente una llamada a IA cuando no se puede usar el wrapper.
    
    Útil para casos donde:
    - Se usa una biblioteca diferente a LangChain
    - Se necesita registrar llamadas de embeddings
    - Se tiene información de uso de forma independiente
    
    Args:
        tokens_entrada: Tokens del prompt
        tokens_salida: Tokens de la respuesta
        tiempo_ejecucion_ms: Tiempo en milisegundos
        app_name: Nombre de la aplicación
        modelo: Modelo usado
        proveedor: Proveedor de IA
        grupo_procesos: ID de agrupación
        status: 'Exito' o 'Fallo'
        
    Returns:
        bool: True si se registró exitosamente
        
    Ejemplo:
        track_manual_call(
            tokens_entrada=150,
            tokens_salida=450,
            tiempo_ejecucion_ms=2300,
            app_name="plataforma-sgd-comite",
            modelo="gpt-4o-mini",
            grupo_procesos="comite_procedimiento_admin_001"
        )
    """
    tracker = get_tracker()
    return tracker.registrar_consumo(
        proveedor=proveedor,
        version_modelo=modelo,
        app=app_name,
        tokens_entrada=tokens_entrada,
        tokens_salida=tokens_salida,
        tokens_cache=tokens_cache,
        tiempo_ejecucion=tiempo_ejecucion_ms,
        status=status,
        grupo_procesos=grupo_procesos
    )
