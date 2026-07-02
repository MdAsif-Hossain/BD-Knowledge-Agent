"""Convert the three HuggingFace datasets into clean, typed SQLite databases.

Run with:  ``python -m src.data.build_databases``

For each dataset we:
  1. download it with ``datasets.load_dataset`` and load it into a pandas DataFrame,
  2. rename the raw columns to meaningful ``snake_case`` names,
  3. coerce each column to the correct SQLite type (TEXT / INTEGER / REAL),
  4. write it to its own SQLite file with an explicit typed schema.

The build is idempotent (tables are replaced) and safe to re-run.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src import config

# --------------------------------------------------------------------------- #
# Dataset definitions
#
# Each column is (source_column, target_column, sqlite_type).  The column order
# here defines the order in the resulting table.
# --------------------------------------------------------------------------- #
DATASET_CONFIGS = [
    {
        "repo": "Mahadih534/Institutional-Information-of-Bangladesh",
        "table": "institutions",
        "path": config.INSTITUTIONS_DB,
        "columns": [
            ("INSTITUTE NAME", "name", "TEXT"),
            ("EIIN", "eiin", "INTEGER"),
            ("INSTITUTE_TYPE", "type", "TEXT"),
            ("DIVISION_ID", "division_id", "INTEGER"),
            ("DIVISION", "division", "TEXT"),
            ("DISTRICT_ID", "district_id", "INTEGER"),
            ("DISTRICT", "district", "TEXT"),
            ("THANA_ID", "thana_id", "INTEGER"),
            ("THANA", "thana", "TEXT"),
            ("UNION_ID", "union_id", "INTEGER"),
            ("UNION_NAME", "union_name", "TEXT"),
            ("MAUZA_ID", "mauza_id", "INTEGER"),
            ("MAUZA_NAME", "mauza_name", "TEXT"),
            ("AREA_STATUS", "area_status", "TEXT"),
            ("GEOGRPYCAL_STATUS", "geographical_status", "TEXT"),  # fix source typo
            ("ADDRESS", "address", "TEXT"),
            ("POST", "post_office", "TEXT"),
            ("MANAGEMENT_TYPE", "management_type", "TEXT"),
            ("MOBILE", "mobile", "TEXT"),
            ("STUDENT_TYPE", "student_type", "TEXT"),
            ("EDUCATION_LEVEL", "education_level", "TEXT"),
            ("AFFILIATION", "affiliation", "TEXT"),
            ("MPO_STATUS", "mpo_status", "TEXT"),
        ],
    },
    {
        "repo": "Mahadih534/all-bangladeshi-hospitals",
        "table": "hospitals",
        "path": config.HOSPITALS_DB,
        "columns": [
            ("Id", "id", "INTEGER"),
            ("Name", "name", "TEXT"),
            ("Name (Bangla)", "name_bangla", "TEXT"),
            ("Code", "code", "INTEGER"),
            ("Agency", "agency", "TEXT"),
            ("Type", "type", "TEXT"),
            ("Division", "division", "TEXT"),
            ("District", "district", "TEXT"),
            ("City Corporation", "city_corporation", "TEXT"),
            ("Upazila", "upazila", "TEXT"),
            ("Paurasava", "paurasava", "TEXT"),
            ("Union", "union_name", "TEXT"),
            ("Private", "is_private", "INTEGER"),
        ],
    },
    {
        "repo": "Mahadih534/Bangladeshi-Restaurant-Data",
        "table": "restaurants",
        "path": config.RESTAURANTS_DB,
        "columns": [
            ("place_id", "place_id", "TEXT"),
            ("name", "name", "TEXT"),
            ("latitude", "latitude", "REAL"),
            ("longitude", "longitude", "REAL"),
            ("rating", "rating", "REAL"),
            ("number_of_reviews", "number_of_reviews", "REAL"),
            ("affluence", "affluence", "REAL"),
            ("address", "address", "TEXT"),
        ],
    },
]


def _coerce_series(series: pd.Series, sqlite_type: str) -> pd.Series:
    """Cast a pandas Series to a Python-native, SQLite-friendly form.

    Missing values become ``None`` (SQL NULL) regardless of the target type.
    """
    if sqlite_type == "INTEGER":
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    if sqlite_type == "REAL":
        return pd.to_numeric(series, errors="coerce").astype("float64")
    # TEXT: keep strings, turn NaN/None into real None.
    text = series.astype("object").where(pd.notna(series), None)
    return text.map(lambda v: None if v is None else str(v))


def _clean_frame(df: pd.DataFrame, columns: list[tuple[str, str, str]]) -> tuple[pd.DataFrame, dict[str, str]]:
    clean = pd.DataFrame()
    dtype_map: dict[str, str] = {}
    for source, target, sqlite_type in columns:
        if source in df.columns:
            series = df[source]
        else:
            print(f"  ! source column '{source}' not found — filling with NULLs")
            series = pd.Series([None] * len(df))
        clean[target] = _coerce_series(series, sqlite_type)
        dtype_map[target] = sqlite_type
    return clean, dtype_map


def build_one(cfg: dict) -> int:
    """Build a single database from its config; return the inserted row count."""
    from datasets import load_dataset

    repo, table, path = cfg["repo"], cfg["table"], Path(cfg["path"])
    print(f"\n> Building '{table}' from {repo}")

    df = load_dataset(repo, split="train").to_pandas()
    print(f"  downloaded {len(df):,} rows, {len(df.columns)} columns")

    clean, dtype_map = _clean_frame(df, cfg["columns"])

    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        clean.to_sql(table, conn, if_exists="replace", index=False, dtype=dtype_map)
        count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

    print(f"  wrote {count:,} rows -> {path}")
    return count


def build_all() -> dict[str, int]:
    """Build all three databases. Returns {table_name: row_count}."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, int] = {}
    for cfg in DATASET_CONFIGS:
        results[cfg["table"]] = build_one(cfg)
    return results


def main() -> None:
    print("=" * 68)
    print(" Building SQLite databases for the Multi-Tool AI Agent (Bangladesh)")
    print("=" * 68)
    results = build_all()
    print("\n" + "-" * 68)
    print(" Done. Summary:")
    for table, count in results.items():
        print(f"   {table:<14} {count:>8,} rows")
    print("-" * 68)


if __name__ == "__main__":
    main()
