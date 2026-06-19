from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from schemas.v1.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services.v1.auth import auth_service
from services.v1.auth.security import create_access_token


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role.name if user.role else "UNKNOWN",
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def handle_login(db: AsyncSession, req: LoginRequest) -> TokenResponse:
    user = await auth_service.authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user_id=user.id, role=user.role.name)
    return TokenResponse(access_token=token, user=_to_user_response(user))


async def handle_register(db: AsyncSession, req: RegisterRequest) -> UserResponse:
    existing = await auth_service.get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role_name = req.role.upper()
    if role_name != "ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only ADMIN role is supported")

    user = await auth_service.create_user(
        db,
        email=req.email,
        username=req.username,
        password=req.password,
        role_name=role_name,
    )
    return _to_user_response(user)


async def handle_me(user: User) -> UserResponse:
    return _to_user_response(user)
