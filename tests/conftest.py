import pytest

from src import config


@pytest.fixture(scope="session")
def dbs_available() -> bool:
    """True when all three SQLite databases have been built."""
    return all(spec["path"].exists() for spec in config.DATABASES.values())


@pytest.fixture
def fake_llm():
    """A no-network fake LLM sufficient to *construct* the chains/tools in tests."""
    from langchain_community.llms.fake import FakeListLLM

    return FakeListLLM(responses=["SELECT 1"])
