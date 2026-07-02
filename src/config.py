"""Central configuration: paths, database registry, and the LLM provider factory.

The single ``get_llm()`` factory keeps the rest of the codebase provider-agnostic —
switch between Google Gemini (free), Groq (free), OpenAI, or Anthropic with one
environment variable (``LLM_PROVIDER``) and no code changes.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

INSTITUTIONS_DB = DATA_DIR / "institutions.db"
HOSPITALS_DB = DATA_DIR / "hospitals.db"
RESTAURANTS_DB = DATA_DIR / "restaurants.db"

# Registry consumed by the tool layer: table name -> (db path, one-line summary).
DATABASES = {
    "institutions": {
        "path": INSTITUTIONS_DB,
        "summary": "Educational & government institutions in Bangladesh "
        "(schools, colleges, madrasahs) with location and management details.",
    },
    "hospitals": {
        "path": HOSPITALS_DB,
        "summary": "Bangladeshi hospitals & health facilities with agency, type, "
        "and administrative location (division/district/upazila).",
    },
    "restaurants": {
        "path": RESTAURANTS_DB,
        "summary": "Bangladeshi restaurants with ratings, review counts, address, "
        "and geo-coordinates.",
    },
}

# --------------------------------------------------------------------------- #
# LLM provider factory
# --------------------------------------------------------------------------- #
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "google").lower()


def _provider_key_env(provider: str) -> str:
    return {
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }.get(provider, "GOOGLE_API_KEY")


def provider_status(provider: str | None = None) -> dict:
    """Return provider name, model, and whether the API key is present (for the UI)."""
    provider = (provider or DEFAULT_PROVIDER).lower()
    key_env = _provider_key_env(provider)
    model = {
        "google": os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
        "groq": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),
    }.get(provider, "gemini-2.0-flash")
    return {
        "provider": provider,
        "model": model,
        "key_env": key_env,
        "has_key": bool(os.getenv(key_env)),
    }


def get_llm(provider: str | None = None):
    """Return a LangChain chat model for the configured provider.

    Note: Claude Opus 4.7/4.8 reject the ``temperature`` parameter (HTTP 400), so
    it is intentionally omitted for Anthropic; the other providers use
    ``temperature=0`` for deterministic SQL generation.
    """
    provider = (provider or DEFAULT_PROVIDER).lower()

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            temperature=0,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        # No temperature — Opus 4.7/4.8 return 400 if it is set.
        return ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"))

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}'. "
        "Use one of: google, groq, openai, anthropic."
    )
