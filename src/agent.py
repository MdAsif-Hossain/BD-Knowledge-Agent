"""The main multi-tool agent.

A LangChain tool-calling ``AgentExecutor`` that routes each question to one of four
tools: the three database tools or the web-search tool.
"""

from __future__ import annotations

try:  # LangChain 1.x moved AgentExecutor/create_tool_calling_agent to langchain_classic
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:  # pragma: no cover
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.config import get_llm
from src.tools.db_tool import build_db_tools
from src.tools.web_search import build_web_search_tool

SYSTEM_PROMPT = """You are a helpful, accurate multi-tool AI assistant for Bangladesh.

You can use these tools:
- InstitutionsDBTool  -> data on educational & government institutions (schools, colleges, madrasahs).
- HospitalsDBTool     -> data on hospitals & health facilities (agency, type, location).
- RestaurantsDBTool   -> data on restaurants (ratings, reviews, address, location).
- WebSearchTool       -> general knowledge from the web.

Routing rules:
- For statistics, counts, lists, or lookups about institutions, hospitals, or restaurants
  in Bangladesh, call the matching database tool.
- For definitions, policies, the role of organizations, history, culture, or anything not
  stored in the databases, call WebSearchTool.
- If a database tool reports that the requested detail is not in its dataset (for example,
  hospital bed counts or a restaurant's cuisine), fall back to WebSearchTool.
- Choose the single most relevant tool. Base your final answer only on tool outputs, keep it
  concise, and briefly mention which source (which dataset or the web) you used.
"""


def build_agent(llm=None, verbose: bool = False) -> AgentExecutor:
    """Build the main AgentExecutor wired to all four tools."""
    llm = llm or get_llm()
    tools = build_db_tools(llm) + [build_web_search_tool()]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=6,
        return_intermediate_steps=True,
    )


def ask(question: str, verbose: bool = False) -> str:
    """Convenience one-shot helper: build an agent and answer a single question."""
    result = build_agent(verbose=verbose).invoke({"input": question})
    return result["output"]
