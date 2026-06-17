"""
Agent definition for the Support Agent.

This module constructs and compiles the agent's graph.
"""

import sys
from pathlib import Path

# Agregar el directorio src al path para imports absolutos
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from langgraph.graph import StateGraph, START, END

# Import absoluto desde agents.support.utils
from agents.support.utils import State, conversation_node, create_tool_node, should_continue


# ====================================================================================
# Graph Construction
# ====================================================================================

def create_graph():
    """
    Crea y compila el grafo del agente de soporte.
    
    Flujo del grafo:
    1. START -> conversation
    2. conversation -> should_continue()
       - Si hay tool_calls -> tools
       - Si no -> END
    3. tools -> conversation (loop back)
    
    Returns:
        Grafo compilado listo para ser ejecutado
    """
    # Crear el tool node
    tool_node = create_tool_node()
    
    # Construir el grafo
    builder = StateGraph(State)
    
    # Agregar nodos
    builder.add_node("conversation", conversation_node)
    builder.add_node("tools", tool_node)
    
    # Definir flujo
    builder.add_edge(START, "conversation")
    builder.add_conditional_edges(
        "conversation",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    builder.add_edge("tools", "conversation")
    
    # Compilar y retornar
    return builder.compile()


# ====================================================================================
# Agent Export
# ====================================================================================

# Crear el agente (grafo compilado)
agent = create_graph()

