"""Password hashing and signed access tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.erros import ConflictError
from app.models import User

PASSWORD_ITERATIONS = 310_000
TOKEN_LIFETIME_SECONDS = 3600


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash suitable for storage."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Compare a candidate password against a stored PBKDF2 hash."""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", maxsplit=3)
        if algorithm != "pbkdf2_sha256":
            return False
        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculated.hex(), digest_hex)


def _secret_key() -> bytes:
    secret = os.getenv("AUTH_SECRET_KEY")
    if not secret:
        raise RuntimeError("AUTH_SECRET_KEY deve estar configurada.")
    return secret.encode("utf-8")


def _encode_token_payload(payload: dict[str, int | str]) -> str:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(serialized).rstrip(b"=").decode("ascii")


def issue_access_token(user_id: str, *, now: int | None = None) -> str:
    """Issue a one-hour HMAC-signed bearer token."""
    issued_at = int(time.time()) if now is None else now
    payload = _encode_token_payload({"sub": user_id, "exp": issued_at + TOKEN_LIFETIME_SECONDS})
    signature = hmac.new(_secret_key(), payload.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{payload}.{encoded_signature}"


def verify_access_token(token: str, *, now: int | None = None) -> str | None:
    """Validate a bearer token and return its user id, if it is valid."""
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
        expected = hmac.new(_secret_key(), payload_part.encode("ascii"), hashlib.sha256).digest()
        padding = "=" * (-len(signature_part) % 4)
        actual = base64.urlsafe_b64decode(signature_part + padding)
        if not hmac.compare_digest(expected, actual):
            return None
        payload_padding = "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part + payload_padding))
        current_time = int(time.time()) if now is None else now
        if not isinstance(payload.get("sub"), str) or payload.get("exp", 0) <= current_time:
            return None
        return payload["sub"]
    except (ValueError, TypeError, json.JSONDecodeError, RuntimeError):
        return None


class AuthenticationService:
    """Authenticates active users and issues bearer tokens."""

    def __init__(self, session: Session):
        self.session = session

    def authenticate(self, email: str, password: str) -> tuple[User, str] | None:
        user = self.session.scalar(select(User).where(User.email == email.lower(), User.active.is_(True)))
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user, issue_access_token(user.id)

    def create_user(self, *, name: str, email: str, password: str, role: str) -> User:
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            active=True,
        )
        self.session.add(user)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Já existe uma conta com este e-mail.") from exc
        return user
