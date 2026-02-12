from __future__ import annotations

from .auth import hash_password
from .db import connect


def seed_default_users(db_path: str) -> None:
    defaults = [
        ("Avery Admin", "admin@recurring.local", hash_password("Admin123!"), "admin"),
        ("Morgan Manager", "manager@recurring.local", hash_password("Manager123!"), "manager"),
        ("Ellis Employee", "employee@recurring.local", hash_password("Employee123!"), "employee"),
    ]

    with connect(db_path) as conn:
        for row in defaults:
            conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(email) DO NOTHING
                """,
                row,
            )
        conn.commit()
