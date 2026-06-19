from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.v1.auth.auth_controller import handle_login, handle_me, handle_register
from db.models.user import User
from db.session import get_db
from schemas.v1.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services.v1.auth.dependencies import get_current_user, require_admin

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await handle_login(db, req)


@router.post("/auth/register", response_model=UserResponse)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserResponse:
    return await handle_register(db, req)


@router.get("/auth/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return await handle_me(user)
