# Libraries
import os
from dotenv import load_dotenv
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Cargar variables de entorno
load_dotenv()

# ====================================================================================
# Setup Vector Store y Tool
# ====================================================================================

# Cargar vector store FAISS
def load_vectorstore():
    """Carga la base de datos vectorial desde cache"""
    cache_path = os.path.join(os.path.dirname(__file__), "../../faiss_cache/transformer_paper")
    
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

# Variables globales para lazy loading
_vectorstore = None
_retriever = None

def get_retriever():
    """Obtiene el retriever con lazy loading"""
    global _vectorstore, _retriever
    if _retriever is None:
        _vectorstore = load_vectorstore()
        _retriever = _vectorstore.as_retriever(search_kwargs={"k": 3})
    return _retriever

# Definir la tool para buscar en el paper
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
    retriever = get_retriever()  # Lazy loading
    docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context

# Lista de tools disponibles
tools = [search_transformer_paper]

# ====================================================================================
# Setup LLM con Tools
# ====================================================================================

# LLM principal con fallback OpenAI -> Ollama
def get_llm():
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )
        _ = llm.invoke("ping")
        return llm
    except Exception:
        llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            temperature=0,
        )
        _ = llm.invoke("ping")
        return llm


llm = get_llm()
llm_with_tools = llm.bind_tools(tools)

# ====================================================================================
# State Definition
# ====================================================================================

class State(MessagesState):
    """Estado del agente RAG"""
    pass

# ====================================================================================
# Nodes
# ====================================================================================

def conversation(state: State):
    """Nodo principal de conversación - Estilo Platzi"""
    new_state: State = {}
    history = state["messages"]
    last_message = history[-1]
    
    # System message
    system_message = (
        "Eres un asistente experto en el paper 'Attention Is All You Need'. "
        "Usa la herramienta search_transformer_paper para buscar información en el paper. "
        "Siempre basa tus respuestas en la información encontrada en el paper."
    )
    
    # Invocar LLM con tools
    ai_message = llm_with_tools.invoke([
        ("system", system_message), 
        ("user", last_message.content)
    ])
    
    new_state["messages"] = [ai_message]
    return new_state

# Crear nodo de tools
tool_node = ToolNode(tools)

# ====================================================================================
# Routing Logic
# ====================================================================================

def should_continue(state: State):
    """Decide si continuar con tools o terminar"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Si el LLM llamó a una tool, ir al nodo de tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Si no, terminar
    return END

# ====================================================================================
# Build Graph
# ====================================================================================

builder = StateGraph(State)

# Agregar nodos
builder.add_node("node_1", conversation)
builder.add_node("tools", tool_node)

# Definir flujo
builder.add_edge(START, 'node_1')
builder.add_conditional_edges('node_1', should_continue, {'tools': 'tools', END: END})
builder.add_edge('tools', 'node_1')

# Compilar agente
agent = builder.compile()


