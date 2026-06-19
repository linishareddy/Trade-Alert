#!/usr/bin/env python3
"""
Create the default test admin user.

  Email:    linisha@example.com
  Password: password
  Username: linisha
  Role:     ADMIN

Usage:
  python3 scripts/create_test_user.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from db.models.role import Role
from db.session import AsyncSessionLocal, Base, engine
from services.v1.auth.auth_service import create_user, ensure_role, get_user_by_email
from services.v1.auth.security import hash_password

EMAIL = "linisha@example.com"
PASSWORD = "password"
USERNAME = "linisha"


async def main() -> None:
    import db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await ensure_role(db, "ADMIN", "Full system access")
        existing = await get_user_by_email(db, EMAIL)

        if existing:
            existing.hashed_password = hash_password(PASSWORD)
            existing.username = USERNAME
            existing.is_active = True
            role_result = await db.execute(select(Role).where(Role.name == "ADMIN"))
            existing.role_id = role_result.scalar_one().id
            await db.commit()
            print(f"Updated admin: {EMAIL} / {USERNAME}")
            return

        user = await create_user(
            db,
            email=EMAIL,
            username=USERNAME,
            password=PASSWORD,
            role_name="ADMIN",
        )
        print(f"Created admin: {user.email} / {user.username}")


if __name__ == "__main__":
    asyncio.run(main())
