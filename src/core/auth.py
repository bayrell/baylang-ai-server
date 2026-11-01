"""Авторизация: регистрация, вход, обновление и отзыв токенов."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import (  # noqa: F401  (re-export)
    get_current_user,
    get_provider_repository,
    get_user_repository,
    security,
)
from core.schemas.auth import (
    AuthResponseSchema,
    LoginSchema,
    LogoutSchema,
    RefreshSchema,
    RegisterSchema,
    TokenPairSchema,
)
from core.security import (
    ACCESS_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    get_refresh_ttl,
    hash_password,
    verify_password,
)
from core.services.provider_service import create_default_provider

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def issue_tokens(user_repo, user_id: int) -> Dict[str, Any]:
    """Выдать пару access/refresh токенов и сохранить refresh-токен в БД."""
    access_token, expires_in = create_access_token(user_id)
    refresh_token = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=get_refresh_ttl())
    await user_repo.save_refresh_token(user_id, refresh_token, expires_at.isoformat())

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.post("/register", response_model=AuthResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterSchema,
    user_repo=Depends(get_user_repository),
    provider_repo=Depends(get_provider_repository),
):
    """Регистрация нового пользователя."""
    email = data.email.strip().lower()

    if await user_repo.find_by_email(email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    password_hash = hash_password(data.password)
    user_id = await user_repo.create(email, data.name.strip(), password_hash)

    # Провайдер по умолчанию — OpenRouter.
    await create_default_provider(provider_repo, user_id)

    tokens = await issue_tokens(user_repo, user_id)
    return {"user": {"id": user_id, "email": email, "name": data.name.strip()}, **tokens}


@router.post("/login", response_model=AuthResponseSchema)
async def login(
    data: LoginSchema,
    user_repo=Depends(get_user_repository),
):
    """Вход по email + пароль."""
    user = await user_repo.find_by_email(data.email.strip().lower())
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    tokens = await issue_tokens(user_repo, user["id"])
    return {
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        **tokens,
    }


@router.post("/refresh", response_model=TokenPairSchema)
async def refresh(
    data: RefreshSchema,
    user_repo=Depends(get_user_repository),
):
    """Выдать новый access-токен по refresh-токену."""
    record = await user_repo.find_refresh_token(data.refresh_token)
    if not record or record.get("revoked"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    expires_at = record.get("expires_at")
    if expires_at:
        try:
            deadline = datetime.fromisoformat(str(expires_at))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if deadline < datetime.now(timezone.utc):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")
        except ValueError:
            pass

    tokens = await issue_tokens(user_repo, record["user_id"])
    return tokens


@router.post("/logout")
async def logout(
    data: LogoutSchema,
    user=Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    """Инвалидировать refresh-токен."""
    if data.refresh_token:
        await user_repo.revoke_refresh_token(data.refresh_token)
    return {"ok": True}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    """Текущий пользователь."""
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "created_at": user.get("created_at"),
    }


__all__ = [
    "router",
    "issue_tokens",
    "get_current_user",
    "ACCESS_TOKEN_TYPE",
]
