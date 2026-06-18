"""
Example usage of the Support Agent.

This script demonstrates how to use the support agent in different ways.
"""

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar el agente
from support import agent


def basic_example():
    """Ejemplo básico de uso del agente."""
    print("=" * 80)
    print("EJEMPLO 1: Uso Básico")
    print("=" * 80)
    
    # Hacer una pregunta
    response = agent.invoke({
        "messages": [("user", "¿Qué es el mecanismo de atención en los transformers?")]
    })
    
    # Obtener la respuesta
    answer = response["messages"][-1].content
    print(f"\nPregunta: ¿Qué es el mecanismo de atención en los transformers?")
    print(f"\nRespuesta: {answer}\n")


def conversation_example():
    """Ejemplo de conversación con múltiples mensajes."""
    print("=" * 80)
    print("EJEMPLO 2: Conversación Multi-turno")
    print("=" * 80)
    
    questions = [
        "¿Qué es un transformer?",
        "¿Cuáles son sus ventajas sobre las RNN?",
        "¿Qué resultados obtuvieron en el paper?"
    ]
    
    for i, question in enumerate(questions, 1):
        response = agent.invoke({
            "messages": [("user", question)]
        })
        
        answer = response["messages"][-1].content
        print(f"\nPregunta {i}: {question}")
        print(f"Respuesta {i}: {answer}\n")
        print("-" * 80)


def streaming_example():
    """Ejemplo con streaming de respuestas."""
    print("=" * 80)
    print("EJEMPLO 3: Streaming")
    print("=" * 80)
    
    print("\nPregunta: Explica cómo funciona el multi-head attention")
    print("\nRespuesta (streaming):")
    
    for chunk in agent.stream({
        "messages": [("user", "Explica cómo funciona el multi-head attention")]
    }):
        if "messages" in chunk:
            for message in chunk["messages"]:
                if hasattr(message, 'content'):
                    print(message.content, end="", flush=True)
    
    print("\n")


def main():
    """Ejecuta todos los ejemplos."""
    try:
        # Ejemplo 1: Uso básico
        basic_example()
        
        # Ejemplo 2: Conversación
        conversation_example()
        
        # Ejemplo 3: Streaming
        # streaming_example()  # Descomentar para probar streaming
        
        print("=" * 80)
        print("✅ Todos los ejemplos se ejecutaron exitosamente!")
        print("=" * 80)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Solución: Ejecuta el notebook 05-rag.ipynb para crear la base de datos vectorial.")
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
