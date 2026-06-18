"""
State definition for the Support Agent.

This module defines the state schema used throughout the agent's graph.
"""

from langgraph.graph import MessagesState


class State(MessagesState):
    """
    Estado del agente de soporte RAG.
    
    Hereda de MessagesState que proporciona:
    - messages: Lista de mensajes en la conversación
    
    Puedes extender este estado con campos adicionales según sea necesario:
    
    Example:
        class State(MessagesState):
            user_id: str  # ID del usuario
            session_id: str  # ID de la sesión
            metadata: dict  # Metadatos adicionales
    """
    pass

