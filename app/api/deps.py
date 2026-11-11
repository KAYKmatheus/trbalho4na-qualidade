"""Reusable authentication and role dependencies for API routes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.servicos.autenticacao import verify_access_token

_bearer_scheme = HTTPBearer(auto_error=False)
_AUTH_FAILURE = "Credenciais inválidas ou sessão expirada."


@dataclass(frozen=True)
class CurrentUser:
    """Non-persistent identity resolved from an active account."""

    id: str
    name: str
    email: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: Session = Depends(get_db),
) -> CurrentUser:
    """Resolve the active user for a valid bearer token."""
    user_id = verify_access_token(credentials.credentials) if credentials else None
    user = session.scalar(select(User).where(User.id == user_id, User.active.is_(True))) if user_id else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_AUTH_FAILURE,
            headers={"WWW-Authenticate": "Bearer"},
        )
    identity = CurrentUser(id=user.id, name=user.name, email=user.email, role=user.role)
    session.rollback()
    return identity


def require_roles(*roles: str) -> Callable[..., CurrentUser]:
    """Build a dependency that requires one of the supplied user roles."""

    def role_dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para esta operação.")
        return user

    return role_dependency
