#!/usr/bin/env python3
"""
Chatbot de consola con memoria LangChain, soporte OpenAI/Ollama y herramientas MCP.
Uso: python src/proofs/chat_mcp.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import sys
import traceback
from pathlib import Path
from typing import Any

import tiktoken
from dotenv import load_dotenv
from langchain_classic.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    ConversationSummaryMemory,
)
from langchain_core._api.deprecation import suppress_langchain_deprecation_warning
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Silenciar aviso de transformers/PyTorch (no usamos modelos HF en este script)
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
logging.getLogger("transformers").setLevel(logging.CRITICAL)

# Cargar variables desde .env en la raíz del proyecto
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
RESET = "\033[0m"
TURN_COLORS = ["\033[36m", "\033[32m", "\033[33m", "\033[35m", "\033[34m", "\033[91m"]
MCP_NOTICE_COLOR = "\033[96m"
WORLD_CUP_SYSTEM_PROMPT = """
Eres un asistente experto en la Copa del Mundo de la FIFA.
Responde siempre en espanol y enfocado en partidos, anios, equipos, marcadores y contexto historico del Mundial.

Responde solo mediante datos obtenidos con herramientas MCP.
- Debes usar herramientas MCP en cada turno antes de responder.
- No inventes datos; toda respuesta debe basarse en salida MCP.
- Si falta un dato clave (por ejemplo, el anio), pide aclaracion breve.

Si la pregunta no es del Mundial, indicarlo brevemente, pero siempre bajo este flujo basado en MCP.
""".strip()


def count_tokens(text: str, model: str) -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text or ""))


def memory_text(memory: Any) -> str:
    data = memory.load_memory_variables({})
    history = data.get("history", "")
    if isinstance(history, list):
        return "\n".join(getattr(m, "content", str(m)) for m in history)
    return str(history)


def build_memory(choice: str, llm: Any) -> Any:
    options = {
        "1": lambda: ConversationBufferMemory(),
        "2": lambda: ConversationBufferWindowMemory(k=4),
        "3": lambda: ConversationSummaryMemory(llm=llm),
        "4": lambda: ConversationSummaryBufferMemory(llm=llm, max_token_limit=500),
    }
    return options[choice]()


def select_memory(llm: Any) -> Any:
    print("\nSelecciona el tipo de memoria:")
    print("  1) Buffer          — historial completo")
    print("  2) Ventana (k=4)   — ultimas 4 interacciones")
    print("  3) Resumen         — resumen progresivo con LLM")
    print("  4) Resumen+Buffer  — recientes en bruto + resumen")
    while True:
        choice = input("\nOpcion [1-4]: ").strip()
        if choice in {"1", "2", "3", "4"}:
            return build_memory(choice, llm)
        print("Opcion no valida.")


def init_llm() -> tuple[Any, str, str]:
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    try:
        llm = ChatOpenAI(
            model=model,
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        _ = llm.invoke("ping")
        return llm, "OpenAI", model
    except Exception:
        model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        llm = ChatOllama(model=model, temperature=0.3)
        try:
            _ = llm.invoke("ping")
            return llm, "Ollama", model
        except Exception as ollama_err:
            print("Error: no se pudo inicializar OpenAI ni Ollama.")
            print("Verifica OPENAI_API_KEY o que Ollama este activo...")
            raise SystemExit(1) from ollama_err


def parse_tool_input(tool_call: dict[str, Any]) -> str:
    tool_args = tool_call.get("args", {})
    if isinstance(tool_args, dict):
        return str(tool_args.get("query", str(tool_args)))
    return str(tool_args)


def build_server_params() -> StdioServerParameters | None:
    mcp_command = os.getenv("MCP_SERVER_COMMAND", sys.executable)
    mcp_args_raw = os.getenv("MCP_SERVER_ARGS", "").strip()
    if not mcp_args_raw:
        print(
            "⚠️ MCP desactivado: define MCP_SERVER_ARGS con la ruta/comando "
            "de tu servidor MCP."
        )
        return None

    server_env = os.environ.copy()
    # Evitar ruido en stdout del servidor MCP (rompe el protocolo stdio).
    server_env.setdefault("FASTMCP_LOG_LEVEL", "ERROR")
    server_env.setdefault("PYTHONUNBUFFERED", "1")
    args = shlex.split(mcp_args_raw)

    print(f"🔧 MCP launch -> command={mcp_command} args={args}")
    return StdioServerParameters(command=mcp_command, args=args, env=server_env)


async def invoke_mcp_tool_async(
    server_params: StdioServerParameters,
    tool_name: str,
    query: str,
) -> str:
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments={"query": query})
            return str(result.content)


def make_mcp_bridge(server_params: StdioServerParameters, tool_name: str, description: str):
    @tool(tool_name, description=description or f"Herramienta MCP: {tool_name}")
    def mcp_bridge_tool(query: str) -> str:
        return asyncio.run(invoke_mcp_tool_async(server_params, tool_name, query))

    return mcp_bridge_tool


def load_mcp_tools() -> list[Any]:
    server_params = build_server_params()
    if not server_params:
        return []

    async def discover() -> list[tuple[str, str]]:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                discovered = await session.list_tools()
                return [(t.name, t.description or "") for t in discovered.tools]

    try:
        discovered_tools = asyncio.run(discover())
        langchain_tools = [
            make_mcp_bridge(server_params, name, description)
            for name, description in discovered_tools
        ]
        if langchain_tools:
            tool_names = ", ".join(t.name for t in langchain_tools)
            print(
                f"🔌 MCP: Vinculadas {len(langchain_tools)} herramientas con exito: "
                f"{tool_names}"
            )
        return langchain_tools
    except Exception as exc:
        print(
            "⚠️ Advertencia MCP: No se pudo conectar al servidor MCP "
            f"({exc}). Continuando sin herramientas."
        )
        print("Detalle del error MCP:")
        traceback.print_exc()
        return []


def run_chat_turn(
    llm_with_tools: Any,
    mcp_tools: list[Any],
    memory: Any,
    user_input: str,
) -> tuple[str, bool]:
    if not mcp_tools:
        return (
            "MCP no esta disponible. Este asistente solo responde mediante herramientas MCP.",
            False,
        )

    history_context = memory.load_memory_variables({}).get("history", "")
    mcp_mode = "habilitado" if mcp_tools else "deshabilitado"
    messages = [
        SystemMessage(
            content=(
                f"{WORLD_CUP_SYSTEM_PROMPT}\n\n"
                f"Estado MCP: {mcp_mode}.\n"
                f"History context:\n{history_context}"
            )
        ),
        HumanMessage(content=user_input),
    ]

    response = llm_with_tools.invoke(messages)

    used_mcp = False
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"🛠️ [MCP ejecutando herramienta: {tool_call['name']}...]")
            target_tool = next((t for t in mcp_tools if t.name == tool_call["name"]), None)
            if not target_tool:
                continue

            used_mcp = True
            tool_result = target_tool.invoke(parse_tool_input(tool_call))
            # OpenAI requiere un ToolMessage ligado al tool_call_id.
            messages.append(response)
            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )
            response = llm_with_tools.invoke(messages)

    if not used_mcp:
        return (
            "No se ejecuto ninguna herramienta MCP en este turno. "
            "Reformula tu pregunta para consultar datos del Mundial (por ejemplo, incluye un anio).",
            False,
        )

    return str(response.content), used_mcp


def main() -> None:
    llm, provider, model = init_llm()
    mcp_tools = load_mcp_tools()
    llm_with_tools = llm.bind_tools(mcp_tools) if mcp_tools else llm

    with suppress_langchain_deprecation_warning():
        memory = select_memory(llm)

    print(f"\nChat iniciado con {provider} ({model}). Escribe 'salir' para terminar.\n")

    turn = 0
    with suppress_langchain_deprecation_warning():
        while True:
            user_input = input("Tu: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"salir", "exit", "quit"}:
                print("Hasta luego.")
                break

            turn += 1
            reply, used_mcp = run_chat_turn(llm_with_tools, mcp_tools, memory, user_input)
            memory.save_context({"input": user_input}, {"output": reply})

            tokens = count_tokens(memory_text(memory), model)
            color = TURN_COLORS[(turn - 1) % len(TURN_COLORS)]
            if used_mcp:
                print(f"{MCP_NOTICE_COLOR}📌 Datos obtenidos desde MCP{RESET}")
            print(f"Asistente: {reply}")
            print(f"{color}📊 Memoria -> {tokens} tokens en este turno{RESET}\n")


if __name__ == "__main__":
    main()