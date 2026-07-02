"""Reusable text-to-SQL tool factory.

``make_db_tool`` turns any single-table SQLite database into a LangChain tool that:
  1. converts a natural-language question into SQL (``create_sql_query_chain``),
  2. blocks anything that is not a read-only ``SELECT`` (defence in depth: the
     SQLite connection itself is opened read-only),
  3. executes the query, and
  4. asks the LLM to phrase the raw result as a natural-language answer.

If the data cannot answer the question, the tool says so clearly — which lets the
main agent fall back to the web-search tool.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

try:  # LangChain 1.x moved the classic chains into langchain_classic
    from langchain.chains import create_sql_query_chain
except ImportError:  # pragma: no cover
    from langchain_classic.chains import create_sql_query_chain

from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from src import config

# Statements that must never run against the read-only databases.
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)
_RESULT_CHAR_LIMIT = 4000  # cap the SQL result text handed back to the LLM


class _DBQuestion(BaseModel):
    """Explicit, named argument schema so tool-calling models fill it reliably."""

    question: str = Field(
        description="The natural-language question to answer from this database."
    )


def _read_only_db(db_path: Path, table: str) -> SQLDatabase:
    """Build a LangChain SQLDatabase backed by a read-only SQLite connection.

    Using a SQLAlchemy ``creator`` avoids URL-encoding problems with file paths
    that contain spaces, and ``mode=ro`` enforces read-only access at the driver
    level, so a stray write would raise rather than mutate data.
    """
    engine = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(
            f"file:{db_path.as_posix()}?mode=ro",
            uri=True,
            check_same_thread=False,
        ),
        poolclass=StaticPool,
    )
    return SQLDatabase(engine, include_tables=[table], sample_rows_in_table_info=3)


def _clean_sql(text: str) -> str:
    """Extract a clean SQL statement from an LLM response.

    Handles models (e.g. Llama) that echo the ``Question: ... SQLQuery: ...``
    scaffold, wrap the query in markdown fences, or append a ``SQLResult:`` label.
    """
    text = text.strip()
    # If the model echoed the scaffold, keep only what follows the SQLQuery: label.
    match = re.search(r"SQLQuery:\s*", text, flags=re.IGNORECASE)
    if match:
        text = text[match.end() :]
    # Drop any trailing SQLResult:/Answer: section the model may add.
    text = re.split(r"\n\s*(?:SQLResult:|Answer:)", text, flags=re.IGNORECASE)[0]
    # Strip markdown code fences.
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text).strip().strip("`").strip()
    # Keep only the first statement.
    return text.split(";")[0].strip()


def _is_safe_select(sql: str) -> bool:
    stripped = sql.strip().lower()
    if not (stripped.startswith("select") or stripped.startswith("with")):
        return False
    return _FORBIDDEN.search(sql) is None


def make_db_tool(
    llm, db_path: Path, table: str, name: str, description: str
) -> StructuredTool:
    """Create a natural-language question-answering Tool over one SQLite table."""
    db_path = Path(db_path)
    db = _read_only_db(db_path, table)
    sql_chain = create_sql_query_chain(llm, db, k=25)

    answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a data analyst answering questions about Bangladesh using the "
                "result of a SQL query. Answer the user's question in clear, concise "
                "natural language based ONLY on the SQL result. If the result is empty "
                "or does not contain the requested detail, say the information is not "
                "available in this dataset.",
            ),
            (
                "human",
                "Question: {question}\nSQL used: {sql}\nSQL result: {result}\n\nAnswer:",
            ),
        ]
    )
    answer_chain = answer_prompt | llm | StrOutputParser()

    def _run(question: str) -> str:
        try:
            raw_sql = sql_chain.invoke({"question": question})
            sql = _clean_sql(raw_sql)
        except Exception as exc:  # noqa: BLE001
            return f"Could not translate the question into SQL for the {table} dataset ({exc})."

        if not _is_safe_select(sql):
            return (
                "For safety, only read-only SELECT queries are allowed; that request "
                "was blocked."
            )

        try:
            result = db.run(sql)
        except Exception as exc:  # noqa: BLE001
            return (
                f"The {table} dataset could not answer that ({exc}). "
                "This detail may not be covered by this dataset."
            )

        if not result or result.strip() in ("", "[]", "()"):
            return f"No matching records were found in the {table} dataset."

        result = result[:_RESULT_CHAR_LIMIT]
        return answer_chain.invoke({"question": question, "sql": sql, "result": result})

    return StructuredTool.from_function(
        func=_run,
        name=name,
        description=description,
        args_schema=_DBQuestion,
    )


# --------------------------------------------------------------------------- #
# Concrete tools required by the spec
# --------------------------------------------------------------------------- #
_TOOL_SPECS = [
    {
        "table": "institutions",
        "name": "InstitutionsDBTool",
        "description": (
            "Answer questions about educational and government INSTITUTIONS in "
            "Bangladesh (schools, colleges, madrasahs). Columns: name, type, "
            "division, district, thana, management_type (Government/Non-Government), "
            "education_level, affiliation, mpo_status, address. Use for counts, lists, "
            "and lookups of institutions by location or type. Input: a natural-language question."
        ),
    },
    {
        "table": "hospitals",
        "name": "HospitalsDBTool",
        "description": (
            "Answer questions about HOSPITALS and health facilities in Bangladesh. "
            "Columns: name, name_bangla, agency (e.g. DGHS), type (e.g. Medical College "
            "Hospital), division, district, city_corporation, upazila, is_private. Use "
            "for counts/lists of hospitals by location, type, or agency. NOTE: the "
            "dataset does NOT include bed counts or doctor numbers. Input: a natural-language question."
        ),
    },
    {
        "table": "restaurants",
        "name": "RestaurantsDBTool",
        "description": (
            "Answer questions about RESTAURANTS in Bangladesh. Columns: name, address, "
            "rating, number_of_reviews, affluence, latitude, longitude. Use for "
            "top-rated restaurants, ratings, review counts, and location via the address "
            "text. NOTE: there is no explicit cuisine or city column — location is matched "
            "from the address text. Input: a natural-language question."
        ),
    },
]


def build_db_tools(llm) -> list[StructuredTool]:
    """Build the three DB-specific tools required by the project spec."""
    tools = []
    for spec in _TOOL_SPECS:
        table = spec["table"]
        tools.append(
            make_db_tool(
                llm=llm,
                db_path=config.DATABASES[table]["path"],
                table=table,
                name=spec["name"],
                description=spec["description"],
            )
        )
    return tools
