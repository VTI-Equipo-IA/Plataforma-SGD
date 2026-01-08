# Script de Ayuda: Actualizar Servidores MCP con Tracking
# Este archivo contiene los cambios necesarios para cada servidor MCP

"""
INSTRUCCIONES:

Para cada servidor MCP (abogado, desarrollador, implementador, secretario),
hacer los siguientes cambios:

================================================================================
PASO 1: Agregar imports al inicio del archivo
================================================================================

# ❌ LÍNEA ACTUAL:
import os

# ✅ AGREGAR DESPUÉS:
import sys

# Y agregar después de todos los imports, antes de "# Config":
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from comite.utils.tracked_llm_mcp import create_mcp_llm


================================================================================
PASO 2: Modificar la función _llm()
================================================================================

Cada servidor tiene una función _llm() similar. Buscar y reemplazar:

# ❌ ANTES:
def _llm(temp: float, max_tokens: Optional[int] = None) -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=temp, max_tokens=max_tokens or None)

# ✅ DESPUÉS:
def _llm(temp: float, max_tokens: Optional[int] = None, grupo_procesos: Optional[str] = None) -> ChatOpenAI:
    '''Crea LLM con tracking automático de consumo.'''
    return create_mcp_llm(
        model=OPENAI_MODEL,
        temperature=temp,
        app_name="comite-NOMBRE",  # Cambiar NOMBRE por: abogado, desarrollador, implementador, secretario
        max_tokens=max_tokens,
        grupo_procesos=grupo_procesos,
        track_enabled=True
    )


================================================================================
PASO 3: Actualizar llamadas a _llm() que necesiten grupo_procesos
================================================================================

En las funciones principales de cada servidor, donde se llama a _llm(), 
opcionalmente pasar el grupo_procesos si está disponible en el contexto:

# EJEMPLO EN UNA FUNCIÓN TOOL:
def generar_intervencion(ctx: Dict[str, Any]) -> Dict[str, Any]:
    # Si existe un ID de proceso en el contexto
    proceso_id = ctx.get('proceso_id') or ctx.get('grupo_procesos')
    
    llm = _llm(temp=TEMP_INTERV, max_tokens=MAXTOK_INTERV, grupo_procesos=proceso_id)
    # ... resto del código


================================================================================
RESUMEN POR ARCHIVO
================================================================================

1. comite/mcp/servers/mcp_server_abogado.py
   - app_name="comite-abogado"
   
2. comite/mcp/servers/mcp_server_desarrollador.py
   - app_name="comite-desarrollador"
   
3. comite/mcp/servers/mcp_server_implementador.py
   - app_name="comite-implementador"
   
4. comite/mcp/servers/mcp_server_secretario.py
   - app_name="comite-secretario"


================================================================================
VERIFICACIÓN
================================================================================

Después de hacer los cambios, probar ejecutando el servidor y verificar:

1. Que no hay errores de import
2. Que las llamadas se registran en la BD consumo_tokens.consumo_api
3. Ejecutar esta query para verificar:

   SELECT app, COUNT(*) as llamadas, SUM(tokens_entrada + tokens_salida) as total_tokens
   FROM consumo_api
   WHERE app LIKE 'comite-%'
   GROUP BY app
   ORDER BY llamadas DESC;


================================================================================
EJEMPLO COMPLETO: mcp_server_abogado.py
================================================================================
"""

EJEMPLO_COMPLETO_ABOGADO = '''
# mcp_server_abogado.py
from __future__ import annotations

import os
import sys  # <-- AGREGADO
import json
import re
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")

# Importar helper de tracking  # <-- AGREGADO
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from comite.utils.tracked_llm_mcp import create_mcp_llm

# =========================
# Configuración
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TEMP_INTERV   = float(os.getenv("ABOGADO_TEMP_INTERV", "0.2"))
TEMP_DECIDE   = float(os.getenv("ABOGADO_TEMP_DECIDE", "0.0"))
TEMP_REVIEW_H = float(os.getenv("ABOGADO_TEMP_REVIEW_H", "0.15"))
TEMP_REVIEW_I = float(os.getenv("ABOGADO_TEMP_REVIEW_I", "0.15"))

MAXTOK_INTERV = int(os.getenv("ABOGADO_MAXTOK_INTERV", "700"))
MAXTOK_DECIDE = int(os.getenv("ABOGADO_MAXTOK_DECIDE", "300"))
MAXTOK_REVIEW_H = int(os.getenv("ABOGADO_MAXTOK_REVIEW_H", "200"))
MAXTOK_REVIEW_I = int(os.getenv("ABOGADO_MAXTOK_REVIEW_I", "200"))

INDICES_DIR   = os.getenv("ABOGADO_INDEX_DIR", "indices/abogado_index")
EMB_MODEL     = os.getenv("ABOGADO_EMB_MODEL", "text-embedding-3-small")

# =========================
# Helpers
# =========================
def _llm(temp: float, max_tokens: Optional[int] = None, grupo_procesos: Optional[str] = None) -> ChatOpenAI:
    """Crea LLM con tracking automático de consumo."""  # <-- MODIFICADO
    return create_mcp_llm(
        model=OPENAI_MODEL,
        temperature=temp,
        app_name="comite-abogado",  # <-- MODIFICADO
        max_tokens=max_tokens,
        grupo_procesos=grupo_procesos,  # <-- MODIFICADO
        track_enabled=True
    )

# ... resto del código sin cambios
'''

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*80)
    print("EJEMPLO COMPLETO PARA mcp_server_abogado.py:")
    print("="*80)
    print(EJEMPLO_COMPLETO_ABOGADO)
