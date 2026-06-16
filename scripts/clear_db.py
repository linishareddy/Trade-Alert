"""
clear_db.py

Clears ALL data from every table in the Trade-Alert database.
Tables are discovered dynamically from the DB, so the script works
even if some migrations haven't been run yet.

Run from the backend/ directory:
    python scripts/clear_db.py

Skip the confirmation prompt (CI/scripts):
    python scripts/clear_db.py --yes
"""

import asyncio
import sys
import os

# ── Make sure backend/ is on the path so imports resolve ───────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.session import engine

RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# Preferred truncation order (children before parents) for any tables that exist.
# Tables NOT in this list are truncated last, alphabetically.
PREFERRED_ORDER = [
    "parsed_signals",
    "signals",
    "raw_alerts",
]


async def get_existing_tables(conn) -> list[str]:
    """Return all user-created tables that currently exist in the DB."""
    result = await conn.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
    ))
    all_tables = [row[0] for row in result.fetchall()]

    # Sort: preferred order first, then any others alphabetically
    ordered = [t for t in PREFERRED_ORDER if t in all_tables]
    extras  = sorted(t for t in all_tables if t not in PREFERRED_ORDER
                     and t != "alembic_version")  # skip migration tracking table
    return ordered + extras


async def get_row_counts(conn, tables: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in tables:
        result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
        counts[table] = result.scalar()
    return counts


async def clear_all_tables(skip_confirm: bool = False) -> None:
    async with engine.connect() as conn:
        print(f"\n{CYAN}{BOLD}Trade-Alert — Database Cleaner{RESET}")
        print("─" * 40)

        # ── Discover tables ─────────────────────────────────────────────────────
        tables = await get_existing_tables(conn)

        if not tables:
            print(f"{YELLOW}No tables found in the database. "
                  f"Have migrations been run?{RESET}\n")
            return

        # ── Show current row counts ─────────────────────────────────────────────
        counts = await get_row_counts(conn, tables)
        total_rows = sum(counts.values())

        print(f"{'Table':<22} {'Rows':>8}")
        print("─" * 32)
        for table, count in counts.items():
            colour = RED if count > 0 else GREEN
            print(f"  {table:<20} {colour}{count:>8}{RESET}")
        print("─" * 32)
        print(f"  {'TOTAL':<20} {YELLOW}{total_rows:>8}{RESET}\n")

        if total_rows == 0:
            print(f"{GREEN}✓ All tables are already empty. Nothing to do.{RESET}\n")
            return

        # ── Confirmation prompt ─────────────────────────────────────────────────
        if not skip_confirm:
            print(f"{RED}{BOLD}⚠  WARNING: This will permanently delete ALL data above!{RESET}")
            answer = input("  Type  YES  to continue: ").strip()
            if answer != "YES":
                print(f"\n{YELLOW}Aborted. No data was deleted.{RESET}\n")
                return

        # ── Truncate ────────────────────────────────────────────────────────────
        print(f"\n{YELLOW}Truncating tables…{RESET}")
        async with conn.begin():
            for table in tables:
                await conn.execute(
                    text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE')
                )
                print(f"  {GREEN}✓{RESET}  {table}")

        # ── Verify ──────────────────────────────────────────────────────────────
        after_counts = await get_row_counts(conn, tables)
        all_clear = all(v == 0 for v in after_counts.values())

        if all_clear:
            print(f"\n{GREEN}{BOLD}✓ All tables cleared successfully.{RESET}\n")
        else:
            print(f"\n{RED}Some tables still have rows — check for errors above.{RESET}")
            for table, count in after_counts.items():
                if count:
                    print(f"  {RED}✗  {table}: {count} rows remaining{RESET}")


def main() -> None:
    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv
    try:
        asyncio.run(clear_all_tables(skip_confirm=skip_confirm))
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted. No data was deleted.{RESET}\n")
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
