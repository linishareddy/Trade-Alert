#!/usr/bin/env python3
"""
Create (or update) an admin user.

Usage:
  python scripts/create_admin.py --email admin@example.com --password 'Secret123'
  python scripts/create_admin.py   # prompts interactively
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from db.models.role import Role
from db.models.user import User
from db.session import AsyncSessionLocal, Base, engine
from services.v1.auth.auth_service import create_user, ensure_role, get_user_by_email
from services.v1.auth.security import hash_password


async def _init() -> None:
    import db.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _run(email: str, password: str, username: str | None) -> None:
    await _init()
    async with AsyncSessionLocal() as db:
        await ensure_role(db, "ADMIN", "Full system access")
        existing = await get_user_by_email(db, email)
        uname = username or email.split("@")[0]

        if existing:
            existing.hashed_password = hash_password(password)
            existing.is_active = True
            role_result = await db.execute(select(Role).where(Role.name == "ADMIN"))
            admin_role = role_result.scalar_one()
            existing.role_id = admin_role.id
            if username:
                existing.username = username
            await db.commit()
            print(f"Updated admin user: {existing.email} ({existing.username})")
            return

        user = await create_user(
            db,
            email=email,
            username=uname,
            password=password,
            role_name="ADMIN",
        )
        print(f"Created admin user: {user.email} ({user.username})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password (min 8 chars)")
    parser.add_argument("--username", help="Display username (defaults to email prefix)")
    args = parser.parse_args()

    email = args.email or input("Email: ").strip()
    if not email:
        print("Email is required", file=sys.stderr)
        sys.exit(1)

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        sys.exit(1)

    asyncio.run(_run(email, password, args.username))


if __name__ == "__main__":
    main()
