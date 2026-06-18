# pip install -qU langchain "langchain[anthropic]"
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def get_llm():
    """Fallback OpenAI -> Ollama."""
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


# Initialize the model
model = get_llm()

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent (commented out - use this when running directly)
# agent.invoke(
#     {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
# )