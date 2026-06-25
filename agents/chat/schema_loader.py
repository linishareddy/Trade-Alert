"""
agents/chat/schema_loader.py

Loads scripts/schema.json once at process startup and converts it into
a compact, LLM-readable text block that is injected into every SQL
generation prompt.

Uses functools.lru_cache so the file is read only once.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "scripts" / "schema.json"


@functools.lru_cache(maxsize=1)
def get_schema_prompt() -> str:
    """Return a compact text description of all DB tables for the LLM."""
    data = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    lines: list[str] = []

    for table in data["tables"]:
        lines.append(f"\nTable: {table['name']}")
        lines.append(f"  Description: {table['description']}")
        for col in table["columns"]:
            nullable = "nullable" if col["nullable"] else "required"
            lines.append(
                f"  - {col['name']} ({col['type']}, {nullable}): {col['description']}"
            )

    return "\n".join(lines)
