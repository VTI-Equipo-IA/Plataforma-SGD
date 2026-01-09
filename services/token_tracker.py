# services/token_tracker.py
"""
Servicio para rastrear y registrar el consumo de tokens de APIs de IA.
Registra métricas en la base de datos consumo_tokens.consumo_api.
"""
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class TokenTracker:
    """
    Clase para registrar consumo de tokens en la base de datos.
    """
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': 'consumo_tokens',  # Base de datos específica para tracking
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }
        self.api_key = os.getenv('OPENAI_API_KEY', 'unknown')
        self.default_provider = os.getenv('AI_PROVIDER', 'OpenAI')
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    def _get_connection(self):
        """Obtiene una conexión a la base de datos de consumo_tokens."""
        return psycopg2.connect(**self.db_config)
    
    def registrar_consumo(
        self,
        proveedor: str,
        version_modelo: str,
        app: str,
        tokens_entrada: Optional[int] = None,
        tokens_salida: Optional[int] = None,
        tokens_cache: Optional[int] = None,
        tiempo_ejecucion: Optional[int] = None,
        status: str = 'Exito',
        grupo_procesos: Optional[str] = None
    ) -> bool:
        """
        Registra un consumo de API en la base de datos.
        
        Args:
            proveedor: Proveedor de IA (OpenAI, Claude, Gemini, etc.)
            version_modelo: Versión del modelo (gpt-4o, claude-3, etc.)
            app: Nombre de la aplicación que hace la llamada
            tokens_entrada: Cantidad de tokens de entrada/prompt
            tokens_salida: Cantidad de tokens de salida/respuesta
            tiempo_ejecucion: Tiempo en milisegundos que tardó la API
            status: Estado de la ejecución ('Exito' o 'Fallo')
            grupo_procesos: Identificador para agrupar múltiples llamadas
            
        Returns:
            bool: True si se registró exitosamente, False en caso contrario
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO consumo_api (
                    api_key, proveedor, version_modelo, grupo_procesos,
                    fecha, app, status, tokens_entrada, tokens_salida, tokens_cache, tiempo_ejecucion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(query, (
                self.api_key[:50],  # Solo primeros 50 caracteres por seguridad
                proveedor,
                version_modelo,
                grupo_procesos,
                datetime.now(),
                app,
                status,
                tokens_entrada,
                tokens_salida,
                tokens_cache,
                tiempo_ejecucion
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️  Error registrando consumo: {e}")
            return False
    
    @contextmanager
    def track_execution(
        self,
        app: str,
        proveedor: Optional[str] = None,
        version_modelo: Optional[str] = None,
        grupo_procesos: Optional[str] = None
    ):
        """
        Context manager para rastrear automáticamente la ejecución de una llamada a IA.
        
        Uso:
            tracker = TokenTracker()
            with tracker.track_execution(app="plataforma-sgd") as track_info:
                response = llm.invoke(prompt)
                track_info['tokens_entrada'] = response.usage.input_tokens
                track_info['tokens_salida'] = response.usage.output_tokens
        """
        start_time = time.time()
        track_info = {
            'tokens_entrada': None,
            'tokens_salida': None,
            'tokens_cache': None,
            'status': 'Exito',
            'proveedor': proveedor or self.default_provider,
            'version_modelo': version_modelo or self.default_model,
            'grupo_procesos': grupo_procesos
        }
        
        try:
            yield track_info
            
        except Exception as e:
            track_info['status'] = 'Fallo'
            raise
            
        finally:
            tiempo_ejecucion = int((time.time() - start_time) * 1000)  # Convertir a milisegundos
            
            self.registrar_consumo(
                proveedor=track_info['proveedor'],
                version_modelo=track_info['version_modelo'],
                app=app,
                tokens_entrada=track_info['tokens_entrada'],
                tokens_salida=track_info['tokens_salida'],
                tokens_cache=track_info['tokens_cache'],
                tiempo_ejecucion=tiempo_ejecucion,
                status=track_info['status'],
                grupo_procesos=track_info['grupo_procesos']
            )


def _extract_cached_tokens_from_mapping(mapping: Dict[str, Any]) -> Optional[int]:
    if not isinstance(mapping, dict):
        return None

    direct = mapping.get('cached_tokens')
    if isinstance(direct, (int, float)):
        return int(direct)

    for nested_key in (
        'prompt_tokens_details',
        'prompt_token_details',
        'input_token_details',
        'input_tokens_details',
        'token_details',
    ):
        nested = mapping.get(nested_key)
        if isinstance(nested, dict):
            val = nested.get('cached_tokens')
            if isinstance(val, (int, float)):
                return int(val)
            # Algunos SDKs usan cache_read
            val = nested.get('cache_read')
            if isinstance(val, (int, float)):
                return int(val)

    return None


def _compute_non_cached_input(total_input: Optional[int], cached: Optional[int]) -> Optional[int]:
    if total_input is None:
        return None
    if cached is None:
        return total_input
    try:
        total_i = int(total_input)
        cached_i = int(cached)
    except Exception:
        return total_input
    if cached_i < 0:
        return total_i
    if cached_i > total_i:
        return total_i
    return total_i - cached_i


def extract_usage_from_response(response: Any) -> Dict[str, Optional[int]]:
    """
    Extrae información de uso de tokens de diferentes tipos de respuestas de LangChain/OpenAI.
    
    Args:
        response: Respuesta de una llamada a LLM (puede ser varios tipos)
        
    Returns:
        Dict con 'tokens_entrada' y 'tokens_salida'
    """
    total_input_tokens = None
    tokens_salida = None
    tokens_cache = None
    
    # Estrategia 1: usage_metadata (LangChain >= 0.2.x)
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        usage = response.usage_metadata
        if isinstance(usage, dict):
            total_input_tokens = usage.get('input_tokens')
            tokens_salida = usage.get('output_tokens')
            tokens_cache = _extract_cached_tokens_from_mapping(usage)
        else:
            total_input_tokens = getattr(usage, 'input_tokens', None)
            tokens_salida = getattr(usage, 'output_tokens', None)
            if tokens_cache is None and hasattr(usage, '__dict__') and isinstance(usage.__dict__, dict):
                tokens_cache = _extract_cached_tokens_from_mapping(usage.__dict__)
    
    # Estrategia 2: response_metadata.token_usage
    if total_input_tokens is None and hasattr(response, 'response_metadata'):
        metadata = response.response_metadata
        if isinstance(metadata, dict) and 'token_usage' in metadata:
            token_usage = metadata['token_usage']
            if isinstance(token_usage, dict):
                total_input_tokens = token_usage.get('prompt_tokens')
                tokens_salida = token_usage.get('completion_tokens')
                if tokens_cache is None:
                    tokens_cache = _extract_cached_tokens_from_mapping(token_usage)
            else:
                total_input_tokens = getattr(token_usage, 'prompt_tokens', None)
                tokens_salida = getattr(token_usage, 'completion_tokens', None)
                if tokens_cache is None and hasattr(token_usage, '__dict__') and isinstance(token_usage.__dict__, dict):
                    tokens_cache = _extract_cached_tokens_from_mapping(token_usage.__dict__)
    
    # Estrategia 3: Atributo usage directo (OpenAI SDK)
    if total_input_tokens is None and hasattr(response, 'usage'):
        usage = response.usage
        if isinstance(usage, dict):
            total_input_tokens = usage.get('prompt_tokens')
            tokens_salida = usage.get('completion_tokens')
            if tokens_cache is None:
                tokens_cache = _extract_cached_tokens_from_mapping(usage)
        else:
            total_input_tokens = getattr(usage, 'prompt_tokens', None)
            tokens_salida = getattr(usage, 'completion_tokens', None)
            if tokens_cache is None and hasattr(usage, '__dict__') and isinstance(usage.__dict__, dict):
                tokens_cache = _extract_cached_tokens_from_mapping(usage.__dict__)
    
    # Estrategia 4: Buscar en __dict__ (último recurso)
    if total_input_tokens is None and hasattr(response, '__dict__'):
        response_dict = response.__dict__
        # Buscar usage_metadata en el dict
        if 'usage_metadata' in response_dict:
            um = response_dict['usage_metadata']
            if isinstance(um, dict):
                total_input_tokens = um.get('input_tokens')
                tokens_salida = um.get('output_tokens')
                if tokens_cache is None:
                    tokens_cache = _extract_cached_tokens_from_mapping(um)

    tokens_entrada = _compute_non_cached_input(
        total_input=int(total_input_tokens) if isinstance(total_input_tokens, (int, float)) else total_input_tokens,
        cached=int(tokens_cache) if isinstance(tokens_cache, (int, float)) else tokens_cache,
    )
    
    return {
        'tokens_entrada': tokens_entrada,
        'tokens_salida': tokens_salida,
        'tokens_cache': tokens_cache,
    }


# Instancia global para uso conveniente
_tracker = None

def get_tracker() -> TokenTracker:
    """Obtiene la instancia global del tracker."""
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker()
    return _tracker
