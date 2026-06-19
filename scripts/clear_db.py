#!/usr/bin/env python3
"""
clear_db.py  —  Wipe ALL rows from every table in the Trade-Alert database.

Usage (from the Trade-Alert/ directory with venv active):

    python scripts/clear_db.py          # shows counts, prompts YES to confirm
    python scripts/clear_db.py --yes    # skip prompt (for scripts/CI)

Tables are truncated with CASCADE, so FK order doesn't matter.
The alembic_version table is never touched.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.session import engine

# ── ANSI colours ─────────────────────────────────────────────────────────────
R = "\033[91m"; Y = "\033[93m"; G = "\033[92m"; C = "\033[96m"
B = "\033[1m";  Z = "\033[0m"


async def run(skip_confirm: bool) -> None:
    async with engine.connect() as conn:

        # ── 1. Discover all user tables (skip alembic_version) ────────────────
        rows = await conn.execute(text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename != 'alembic_version' "
            "ORDER BY tablename"
        ))
        tables = [r[0] for r in rows.fetchall()]

        if not tables:
            print(f"\n{Y}No tables found — have migrations been run?{Z}\n")
            return

        # ── 2. Count rows ─────────────────────────────────────────────────────
        counts: dict[str, int] = {}
        for t in tables:
            res = await conn.execute(text(f'SELECT COUNT(*) FROM "{t}"'))
            counts[t] = res.scalar()

        total = sum(counts.values())

        # ── 3. Print summary ─────────────────────────────────────────────────
        print(f"\n{C}{B}Trade-Alert — Database Cleaner{Z}")
        print("─" * 38)
        print(f"  {'Table':<22} {'Rows':>6}")
        print("  " + "─" * 30)
        for t, n in counts.items():
            colour = R if n > 0 else G
            print(f"  {t:<22} {colour}{n:>6}{Z}")
        print("  " + "─" * 30)
        print(f"  {'TOTAL':<22} {Y}{total:>6}{Z}\n")

        if total == 0:
            print(f"{G}✓ Already empty — nothing to do.{Z}\n")
            return

        # ── 4. Confirm ────────────────────────────────────────────────────────
        if not skip_confirm:
            print(f"{R}{B}⚠  This will permanently delete ALL data shown above.{Z}")
            ans = input("  Type  YES  to continue (anything else aborts): ").strip()
            if ans != "YES":
                print(f"\n{Y}Aborted — no data deleted.{Z}\n")
                return

        # ── 5. Truncate (CASCADE handles all FK constraints) ─────────────────
        # Commit the read transaction first so we can start a fresh write txn.
        await conn.commit()

        print(f"\n{Y}Clearing tables…{Z}")
        for t in tables:
            await conn.execute(
                text(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE')
            )
            print(f"  {G}✓{Z}  {t}  ({counts[t]} rows deleted)")
        await conn.commit()

        # ── 6. Verify ─────────────────────────────────────────────────────────
        remaining: dict[str, int] = {}
        for t in tables:
            res = await conn.execute(text(f'SELECT COUNT(*) FROM "{t}"'))
            remaining[t] = res.scalar()
        await conn.commit()

        leftovers = {t: n for t, n in remaining.items() if n > 0}
        if leftovers:
            print(f"\n{R}Some tables still have rows:{Z}")
            for t, n in leftovers.items():
                print(f"  {R}✗  {t}: {n} rows{Z}")
        else:
            print(f"\n{G}{B}✅  All tables cleared successfully.{Z}\n")


def main() -> None:
    skip = "--yes" in sys.argv or "-y" in sys.argv
    try:
        asyncio.run(run(skip_confirm=skip))
    except KeyboardInterrupt:
        print(f"\n{Y}Interrupted — no data deleted.{Z}\n")


if __name__ == "__main__":
    main()
