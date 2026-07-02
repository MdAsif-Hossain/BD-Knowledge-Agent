import sqlite3

import pytest

from src.data.build_databases import DATASET_CONFIGS


@pytest.mark.parametrize("cfg", DATASET_CONFIGS, ids=lambda c: c["table"])
def test_database_schema_and_rows(cfg):
    path = cfg["path"]
    if not path.exists():
        pytest.skip(f"{path} not built — run `python -m src.data.build_databases`")

    conn = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert cfg["table"] in tables, f"table {cfg['table']} missing"

        info = list(conn.execute(f'PRAGMA table_info("{cfg["table"]}")'))
        col_types = {row[1]: (row[2] or "").upper() for row in info}

        for _source, target, sqlite_type in cfg["columns"]:
            assert target in col_types, f"column {target} missing"
            assert sqlite_type in col_types[target], (
                f"{target}: declared type '{col_types[target]}' != '{sqlite_type}'"
            )

        count = conn.execute(f'SELECT COUNT(*) FROM "{cfg["table"]}"').fetchone()[0]
        assert count > 0, f"{cfg['table']} is empty"
    finally:
        conn.close()
