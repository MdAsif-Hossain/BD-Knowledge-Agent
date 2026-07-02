"""Web-search tool for general-knowledge queries.

Defaults to **DuckDuckGo** (no API key required, free). If ``TAVILY_API_KEY`` is
set, it transparently upgrades to Tavily for higher-quality results.
"""

from __future__ import annotations

import os

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

_DESCRIPTION = (
    "Search the web for GENERAL KNOWLEDGE about Bangladesh that is NOT in the local "
    "databases: definitions, government policies, the role of organizations (e.g. the "
    "role of DGHS), history, culture, and current events. Also use this as a fallback "
    "when a database tool reports that a detail is not in its dataset. "
    "Input: a search query or question."
)


class _SearchQuery(BaseModel):
    """Explicit, named argument schema so tool-calling models fill it reliably."""

    query: str = Field(description="The search query or question to look up on the web.")


def _duckduckgo_search(query: str, max_results: int = 5) -> str:
    """Keyless DuckDuckGo search, resilient to the duckduckgo-search -> ddgs rename."""
    try:
        from ddgs import DDGS  # newer package name
    except ImportError:  # pragma: no cover - depends on installed version
        from duckduckgo_search import DDGS  # legacy package name

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:  # noqa: BLE001
        return f"Web search failed: {exc}"

    if not results:
        return "No web results found."

    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('body', '')}\n{r.get('href', '')}".strip()
        for r in results
    )


def build_web_search_tool() -> StructuredTool:
    """Return the WebSearchTool (Tavily if a key is set, else DuckDuckGo)."""
    if os.getenv("TAVILY_API_KEY"):
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            tavily = TavilySearchResults(max_results=5)

            def _tavily_run(query: str) -> str:
                return str(tavily.invoke(query))

            return StructuredTool.from_function(
                func=_tavily_run,
                name="WebSearchTool",
                description=_DESCRIPTION,
                args_schema=_SearchQuery,
            )
        except Exception:  # noqa: BLE001 - fall back to DuckDuckGo
            pass

    def _run(query: str) -> str:
        return _duckduckgo_search(query)

    return StructuredTool.from_function(
        func=_run,
        name="WebSearchTool",
        description=_DESCRIPTION,
        args_schema=_SearchQuery,
    )
