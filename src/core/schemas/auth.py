"""Схемы авторизации."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$"


class RegisterSchema(BaseModel):
    """Тело запроса регистрации."""

    email: str = Field(..., examples=["user@example.com"])
    name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        import re

        email = (value or "").strip().lower()
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Некорректный email")
        return email

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = (value or "").strip()
        if not name:
            raise ValueError("Имя не может быть пустым")
        return name


class LoginSchema(BaseModel):
    """Тело запроса входа."""

    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return (value or "").strip().lower()


class RefreshSchema(BaseModel):
    """Тело запроса обновления токена."""

    refresh_token: str = Field(..., min_length=1)


class LogoutSchema(BaseModel):
    """Тело запроса выхода."""

    refresh_token: str = Field(default="", min_length=0)


class UserOut(BaseModel):
    """Публичные данные пользователя."""

    id: int
    email: str
    name: str
    created_at: Optional[str] = None


class TokenPairSchema(BaseModel):
    """Пара токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class AuthResponseSchema(BaseModel):
    """Ответ на регистрацию/вход."""

    user: Dict[str, Any]
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


__all__ = [
    "RegisterSchema",
    "LoginSchema",
    "RefreshSchema",
    "LogoutSchema",
    "UserOut",
    "TokenPairSchema",
    "AuthResponseSchema",
]
