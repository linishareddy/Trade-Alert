from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.role import Role
from db.models.user import User
from services.v1.auth.security import hash_password, verify_password


async def get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def ensure_role(db: AsyncSession, name: str, description: str | None = None) -> Role:
    role = await get_role_by_name(db, name)
    if role:
        return role
    role = Role(name=name, description=description)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    password: str,
    role_name: str,
) -> User:
    role = await ensure_role(db, role_name)
    user = User(
        email=email.lower(),
        username=username,
        hashed_password=hash_password(password),
        role_id=role.id,
    )
    db.add(user)
    await db.commit()
    reloaded = await get_user_by_id(db, user.id)
    assert reloaded is not None
    return reloaded
