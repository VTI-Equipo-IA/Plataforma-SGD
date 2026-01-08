# build_indices.py
from rag_loader import build_index_for_folder, load_retriever
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Definimos carpetas de origen y destino
CONFIG = {
    "abogado": ("docs/abogado", "indices/abogado_index"),
    "pmg": ("docs/pmg", "indices/pmg_index"),
    "desarrollador": ("docs/desarrollador", "indices/desarrollador_index"),
    "secretario": ("docs/secretario", "indices/secretario_index"),
    "implementador": ("docs/implementador", "indices/implementador_index")
}

retrievers = {}

for agente, (doc_folder, idx_folder) in CONFIG.items():
    print(f"Construyendo índice para {agente}...")
    build_index_for_folder(doc_folder, idx_folder)
    retrievers[agente] = load_retriever(idx_folder)

# Ahora retrievers["abogado"] es una función query->texto contextual
