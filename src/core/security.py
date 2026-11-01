"""Хеширование паролей (bcrypt) и работа с JWT-токенами."""

from __future__ import annotations

import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from core.config import Env
from core.container import container

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

JWT_ALGORITHM = "HS256"
DEFAULT_JWT_SECRET = "baylang-dev-secret-change-me"
DEFAULT_ACCESS_TTL = 60 * 30          # 30 минут
DEFAULT_REFRESH_TTL = 60 * 60 * 24 * 7  # 7 дней
BCRYPT_MAX_BYTES = 72


# ----------------------------------------------------------------------
# Настройки
# ----------------------------------------------------------------------
def _env() -> Env:
    """Текущее окружение приложения."""
    if container.has("env"):
        return container.get("env")
    return Env(os.environ)


def get_jwt_secret() -> str:
    """Секрет для подписи JWT."""
    return _env().get("JWT_SECRET", DEFAULT_JWT_SECRET)


def get_access_ttl() -> int:
    """TTL access-токена в секундах."""
    return _env().get_int("ACCESS_TOKEN_TTL", DEFAULT_ACCESS_TTL)


def get_refresh_ttl() -> int:
    """TTL refresh-токена в секундах."""
    return _env().get_int("REFRESH_TOKEN_TTL", DEFAULT_REFRESH_TTL)


def _bcrypt_rounds() -> int:
    return _env().get_int("BCRYPT_ROUNDS", 12)


# ----------------------------------------------------------------------
# Пароли
# ----------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Захешировать пароль алгоритмом bcrypt."""
    payload = (password or "").encode("utf-8")[:BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt(rounds=_bcrypt_rounds())
    return bcrypt.hashpw(payload, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Проверить пароль против bcrypt-хеша."""
    if not password or not password_hash:
        return False
    payload = (password or "").encode("utf-8")[:BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(payload, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ----------------------------------------------------------------------
# Токены
# ----------------------------------------------------------------------
def create_access_token(user_id: int, expires_in: Optional[int] = None) -> Tuple[str, int]:
    """Создать подписанный JWT access-токен."""
    ttl = int(expires_in if expires_in is not None else get_access_ttl())
    issued_at = int(time.time())
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": issued_at,
        "exp": issued_at + ttl,
        "jti": secrets.token_urlsafe(8),
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, ttl


def create_refresh_token() -> str:
    """Создать непрозрачный refresh-токен (хранится в БД и может быть отозван)."""
    return secrets.token_urlsafe(48)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодировать JWT. Возвращает None, если токен невалиден или просрочен."""
    if not token:
        return None
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def decode_user_id(token: str) -> Optional[int]:
    """Извлечь user_id из JWT-токена."""
    payload = decode_token(token)
    if not payload:
        return None
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError):
        return None


__all__ = [
    "ACCESS_TOKEN_TYPE",
    "REFRESH_TOKEN_TYPE",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "decode_user_id",
    "get_access_ttl",
    "get_refresh_ttl",
    "get_jwt_secret",
    "hash_password",
    "verify_password",
]
