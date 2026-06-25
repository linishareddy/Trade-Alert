"""
agents/chat/tools/text_to_sql.py

Tool 1 — Text-to-SQL

Takes a natural language question, asks Groq to write a safe SELECT query
using the DB schema, executes it on PostgreSQL, and returns raw rows.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from groq import Groq
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.chat.schema_loader import get_schema_prompt
from config.settings import settings
from services.v1.config.runtime_settings import runtime

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "chat_sql_generator.txt"

# Verbs that are never allowed in generated SQL
_BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def _load_sql_prompt(question: str) -> str:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        template
        .replace("{{schema}}", get_schema_prompt())
        .replace("{{question}}", question)
    )


async def text_to_sql(question: str, db: AsyncSession) -> dict:
    """
    Convert a natural language question to SQL via Groq, execute it, and
    return the raw rows as a JSON-serialisable dict.
    """
    groq_key = str(runtime.get("groq_key") or settings.GROQ_API_KEY).strip()
    if not groq_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    prompt = _load_sql_prompt(question)
    client = Groq(api_key=groq_key)

    # Ask Groq to generate the SQL (run sync Groq in thread to keep async loop free)
    response = await asyncio.to_thread(
        client.chat.completions.create,
        messages=[{"role": "user", "content": prompt}],
        model=str(runtime.get("ai_model") or "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=512,
    )
    sql = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model wrapped the SQL
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql).strip()

    logger.info("[ChatTool/text_to_sql] Generated SQL: %s", sql[:200])

    # Safety gate — only allow SELECT statements
    if not sql.upper().lstrip().startswith("SELECT"):
        raise ValueError(f"text_to_sql: generated query is not a SELECT: {sql[:80]}")
    if _BLOCKED_KEYWORDS.search(sql):
        raise ValueError("text_to_sql: blocked keyword found in generated SQL.")

    # Execute
    result = await db.execute(text(sql))
    columns = list(result.keys())
    rows = [dict(zip(columns, row)) for row in result.fetchall()]

    logger.info("[ChatTool/text_to_sql] Returned %d rows.", len(rows))
    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "count": len(rows),
    }
