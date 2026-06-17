"""
Tools for the Support Agent.

This module defines the tools/functions that the agent can use.
"""

import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.tools import tool


# ====================================================================================
# Configuration (inline para evitar dependencia circular)
# ====================================================================================

DEFAULT_CACHE_PATH = "../../../../faiss_cache/transformer_paper"
DEFAULT_RETRIEVER_K = 3


# ====================================================================================
# Vector Store Setup
# ====================================================================================

# Variables globales para lazy loading
_vectorstore = None
_retriever = None


def load_vectorstore(cache_path: str = None):
    """
    Carga la base de datos vectorial desde cache.
    
    Args:
        cache_path: Ruta al cache (opcional, usa config por defecto si no se especifica)
        
    Returns:
        Vectorstore FAISS cargado
        
    Raises:
        FileNotFoundError: Si no se encuentra la base de datos
    """
    if cache_path is None:
        cache_path = DEFAULT_CACHE_PATH
    
    # Resolver ruta relativa
    if not os.path.isabs(cache_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cache_path = os.path.join(current_dir, cache_path)
        cache_path = os.path.normpath(cache_path)
    
    # Verificar si existe el directorio y el archivo index.faiss
    index_file = os.path.join(cache_path, "index.faiss")
    if not os.path.exists(cache_path) or not os.path.exists(index_file):
        raise FileNotFoundError(
            f"❌ Base de datos vectorial no encontrada en {cache_path}\n"
            "Por favor, ejecuta primero el notebook 05-rag.ipynb para crear la base de datos."
        )
    
    vectorstore = FAISS.load_local(
        cache_path, 
        OllamaEmbeddings(model=os.getenv("EMB_MODEL", "nomic-embed-text:latest")),
        allow_dangerous_deserialization=True
    )
    
    return vectorstore


def get_retriever(k: int = None):
    """
    Obtiene el retriever con lazy loading.
    
    Args:
        k: Número de documentos a recuperar (opcional)
        
    Returns:
        Retriever configurado
    """
    global _vectorstore, _retriever
    
    if k is None:
        k = DEFAULT_RETRIEVER_K
    
    # Si el retriever no existe o k ha cambiado, recrear
    if _retriever is None:
        _vectorstore = load_vectorstore()
        _retriever = _vectorstore.as_retriever(search_kwargs={"k": k})
    
    return _retriever


# ====================================================================================
# Tool Definitions
# ====================================================================================

@tool
def search_transformer_paper(query: str) -> str:
    """
    Busca información en el paper 'Attention Is All You Need'.
    
    Usa esta herramienta cuando necesites información sobre:
    - Arquitectura Transformer
    - Mecanismo de atención (attention mechanism)
    - Multi-head attention
    - Positional encoding
    - Resultados y BLEU scores
    - Detalles del entrenamiento
    
    Args:
        query: La pregunta o consulta sobre el paper
        
    Returns:
        Contexto relevante del paper
    """
    retriever = get_retriever()
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context


# ====================================================================================
# Tool Registry
# ====================================================================================

# Lista de todas las tools disponibles
TOOLS: List = [search_transformer_paper]


def get_tools() -> List:
    """
    Obtiene la lista de tools disponibles.
    
    Returns:
        Lista de tools
    """
    return TOOLS

