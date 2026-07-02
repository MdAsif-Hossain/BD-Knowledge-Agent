"""Streamlit chat UI for the Multi-Tool AI Agent for Bangladesh.

Run locally with:  ``streamlit run app.py``
Deploys as-is to Streamlit Community Cloud (add your LLM key in the app secrets).
"""

from __future__ import annotations

import streamlit as st

from src import config
from src.agent import build_agent

st.set_page_config(
    page_title="Multi-Tool AI Agent · Bangladesh",
    page_icon="🇧🇩",
    layout="centered",
)

EXAMPLE_QUERIES = [
    "How many hospitals are there in Dhaka district?",
    "List 5 institutions in Rajshahi division.",
    "Which restaurants have the highest ratings?",
    "What is the role of DGHS in Bangladesh?",
    "How many government institutions are there?",
]


@st.cache_resource(show_spinner=False)
def _load_agent(provider: str):
    """Build (and cache) the agent for the selected provider."""
    return build_agent(llm=config.get_llm(provider), verbose=False)


def _tool_trace(intermediate_steps) -> list[str]:
    """Return the ordered list of tool names the agent invoked."""
    names = []
    for action, _observation in intermediate_steps or []:
        tool = getattr(action, "tool", None)
        if tool:
            names.append(tool)
    return names


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Configuration")
    status = config.provider_status()
    st.markdown(f"**LLM provider:** `{status['provider']}`")
    st.markdown(f"**Model:** `{status['model']}`")
    if status["has_key"]:
        st.success(f"{status['key_env']} detected ✔")
    else:
        st.error(
            f"No `{status['key_env']}` found. Add it to your `.env` "
            "(or Streamlit secrets) to enable the agent."
        )

    st.divider()
    st.subheader("💡 Try an example")
    for example in EXAMPLE_QUERIES:
        if st.button(example, use_container_width=True):
            st.session_state["pending"] = example

    st.divider()
    st.caption(
        "Tools: InstitutionsDBTool · HospitalsDBTool · RestaurantsDBTool · WebSearchTool"
    )


# --------------------------------------------------------------------------- #
# Main chat
# --------------------------------------------------------------------------- #
st.title("🇧🇩 Multi-Tool AI Agent for Bangladesh")
st.caption(
    "Ask about **institutions**, **hospitals**, or **restaurants** (answered from local "
    "SQLite databases), or **general knowledge** (answered via web search). The agent "
    "routes each question to the right tool."
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("tools"):
            st.caption("🛠️ Tools used: " + ", ".join(message["tools"]))

question = st.chat_input("Ask me anything about Bangladesh…")
if not question and "pending" in st.session_state:
    question = st.session_state.pop("pending")

if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    if not status["has_key"]:
        answer = (
            f"⚠️ I can't answer yet — no `{status['key_env']}` is configured. "
            "Add a free API key to start."
        )
        tools_used: list[str] = []
        with st.chat_message("assistant"):
            st.markdown(answer)
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    agent = _load_agent(status["provider"])
                    result = agent.invoke({"input": question})
                    answer = result["output"]
                    tools_used = _tool_trace(result.get("intermediate_steps"))
                except Exception as exc:  # noqa: BLE001
                    answer = f"Something went wrong: {exc}"
                    tools_used = []
            st.markdown(answer)
            if tools_used:
                st.caption("🛠️ Tools used: " + ", ".join(tools_used))

    st.session_state["messages"].append(
        {"role": "assistant", "content": answer, "tools": tools_used}
    )
