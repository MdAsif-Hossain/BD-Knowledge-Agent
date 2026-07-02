import pytest

from src.tools.db_tool import build_db_tools


def test_build_db_tools_names(dbs_available, fake_llm):
    if not dbs_available:
        pytest.skip("databases not built — run `python -m src.data.build_databases`")

    tools = build_db_tools(fake_llm)
    assert [t.name for t in tools] == [
        "InstitutionsDBTool",
        "HospitalsDBTool",
        "RestaurantsDBTool",
    ]
    for tool in tools:
        assert tool.description
