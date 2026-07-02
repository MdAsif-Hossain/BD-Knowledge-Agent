from src.tools.db_tool import _clean_sql, _is_safe_select
from src.tools.web_search import build_web_search_tool


def test_clean_sql_strips_fences_label_and_trailing():
    assert _clean_sql("```sql\nSELECT * FROM t;\n```") == "SELECT * FROM t"
    assert _clean_sql("SQLQuery: SELECT 1") == "SELECT 1"
    assert _clean_sql("SELECT a FROM t; DROP TABLE t") == "SELECT a FROM t"


def test_is_safe_select_allows_reads():
    assert _is_safe_select("SELECT * FROM hospitals")
    assert _is_safe_select("WITH x AS (SELECT 1) SELECT * FROM x")


def test_is_safe_select_blocks_writes():
    for bad in (
        "DELETE FROM t",
        "DROP TABLE t",
        "UPDATE t SET a = 1",
        "INSERT INTO t VALUES (1)",
        "select * from t; drop table t",
        "ALTER TABLE t ADD COLUMN c TEXT",
    ):
        assert not _is_safe_select(bad), bad


def test_web_search_tool_builds():
    tool = build_web_search_tool()
    assert tool.name == "WebSearchTool"
    assert "web" in tool.description.lower()
