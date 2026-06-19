from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Permite ejecutar con: streamlit run src/app/streamlit_app.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.agents.worldcup_graph import ask_worldcup_graph
from src.logs import get_logger, short_text
from src.utils.langsmith_setup import configure_langsmith

MEMORY_WINDOW = 5
DEFAULT_MODEL = "llama3.2:3b"
logger = get_logger("worldcup_streamlit")
LANGSMITH_ENABLED = configure_langsmith()


def _present_answer(answer: str) -> str:
    text = (answer or "").strip()
    for tag in ("[TOOLS]", "[RAG]", "[CHAT]"):
        if text.startswith(tag):
            return text[len(tag):].lstrip()
    return text


st.set_page_config(page_title="WorldCup Graph Bot", page_icon="⚽", layout="centered")
st.title("⚽ WorldCup Graph Bot")
st.caption("Flujo: Guardrails -> Router LLM -> Tools o RAG")
if LANGSMITH_ENABLED:
    st.caption("LangSmith tracing: activo")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Configuracion")
    model_name = st.text_input("Modelo Ollama", value=DEFAULT_MODEL)
    st.caption(f"Memoria activa: ultimos {MEMORY_WINDOW} mensajes")
    if st.button("Nueva conversacion", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Pregunta sobre Mundiales...")

if prompt:
    logger.info("UI user prompt | text=%s", short_text(prompt))
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history_for_graph = st.session_state.messages[-MEMORY_WINDOW:]

    with st.chat_message("assistant"):
        with st.spinner("Procesando en el grafo..."):
            try:
                answer = ask_worldcup_graph(
                    question=prompt,
                    chat_history=history_for_graph,
                    model_name=model_name.strip() or DEFAULT_MODEL,
                )
            except Exception as exc:
                answer = f"Error ejecutando el bot: {exc}"
                logger.exception("UI bot error")
        logger.info("UI assistant answer | text=%s", short_text(answer))
        st.markdown(_present_answer(answer))

    st.session_state.messages.append({"role": "assistant", "content": answer})
