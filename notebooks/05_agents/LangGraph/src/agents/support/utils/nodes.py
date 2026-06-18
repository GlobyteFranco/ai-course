"""
Node definitions for the Support Agent.

This module contains all node functions that process the state.
"""

from langgraph.graph import END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import os

from .state import State
from .tools import get_tools


# ====================================================================================
# Configuration (inline)
# ====================================================================================

DEFAULT_TEMPERATURE = 0.0

# System prompt
SYSTEM_PROMPT = """Eres un asistente experto en el paper 'Attention Is All You Need'. 
Usa la herramienta search_transformer_paper para buscar información en el paper. 
Siempre basa tus respuestas en la información encontrada en el paper."""


# ====================================================================================
# LLM Management (inline para evitar dependencias)
# ====================================================================================

_llm = None
_llm_with_tools = None


def get_llm():
    """Obtiene el LLM con lazy loading."""
    global _llm
    if _llm is None:
        try:
            _llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=DEFAULT_TEMPERATURE,
            )
            _ = _llm.invoke("ping")
        except Exception:
            _llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
                temperature=DEFAULT_TEMPERATURE,
            )
            _ = _llm.invoke("ping")
    return _llm


def get_llm_with_tools():
    """Obtiene el LLM con tools bindeadas."""
    global _llm_with_tools
    if _llm_with_tools is None:
        llm = get_llm()
        tools = get_tools()
        _llm_with_tools = llm.bind_tools(tools)
    return _llm_with_tools


# ====================================================================================
# Node Functions
# ====================================================================================

def conversation_node(state: State) -> dict:
    """
    Nodo principal de conversación.
    
    Este nodo:
    1. Recibe el estado actual con el historial de mensajes
    2. Obtiene el último mensaje del usuario
    3. Invoca el LLM con las tools disponibles
    4. Retorna la respuesta del LLM
    
    Args:
        state: Estado actual del agente
        
    Returns:
        Diccionario con los nuevos mensajes a agregar al estado
    """
    # Obtener historial y último mensaje
    history = state["messages"]
    last_message = history[-1]
    
    # Obtener LLM con tools
    llm_with_tools = get_llm_with_tools()
    
    # Invocar LLM con el system prompt y el mensaje del usuario
    ai_message = llm_with_tools.invoke([
        ("system", SYSTEM_PROMPT), 
        ("user", last_message.content)
    ])
    
    # Retornar nuevo estado con el mensaje del AI
    return {"messages": [ai_message]}


def create_tool_node() -> ToolNode:
    """
    Crea el nodo de herramientas.
    
    Este nodo ejecuta las tools cuando el LLM las invoca.
    
    Returns:
        ToolNode configurado con las tools disponibles
    """
    tools = get_tools()
    return ToolNode(tools)


# ====================================================================================
# Routing Functions
# ====================================================================================

def should_continue(state: State) -> str:
    """
    Función de routing que decide el siguiente paso.
    
    Lógica:
    - Si el último mensaje tiene tool_calls -> ir a "tools"
    - Si no -> terminar (END)
    
    Args:
        state: Estado actual del agente
        
    Returns:
        "tools" si hay tool calls, END si no
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Si el LLM llamó a una tool, ir al nodo de tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Si no, terminar
    return END

