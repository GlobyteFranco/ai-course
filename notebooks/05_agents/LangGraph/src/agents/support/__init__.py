"""
Support Agent - RAG-based assistant for 'Attention Is All You Need' paper.

This module provides a LangGraph agent that can answer questions about
the Transformer paper using RAG (Retrieval Augmented Generation).

Usage:
    from agents.support import agent
    
    # Invocar el agente
    result = agent.invoke({"messages": [("user", "What is attention?")]})
    print(result["messages"][-1].content)

Structure (following LangGraph best practices):
    support/
    ├── utils/              # Utilities for the graph
    │   ├── __init__.py
    │   ├── state.py        # State definition
    │   ├── tools.py        # Tools for the graph
    │   └── nodes.py        # Node functions
    ├── __init__.py         # This file
    └── agent.py            # Graph construction
"""

from .agent import agent, create_graph
from .utils import State, search_transformer_paper, conversation_node, should_continue

__all__ = [
    # Main exports
    "agent",
    "create_graph",
    
    # State
    "State",
    
    # Tools
    "search_transformer_paper",
    
    # Nodes
    "conversation_node",
    "should_continue",
]

__version__ = "1.0.0"
