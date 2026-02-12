from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass
class SessionUser:
    user_id: int
    full_name: str
    email: str
    role: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def make_session_token() -> str:
    return secrets.token_urlsafe(24)
