"""
Level 4 - Expert: Security Testing — SAST Anti-Patterns & Secure Alternatives
==============================================================================
This file demonstrates common security vulnerabilities that static analysis
tools like Bandit detect, alongside their secure alternatives.

WARNING: The insecure examples below are intentionally vulnerable.
         NEVER use them in production code.

Run Bandit:
    pip install bandit
    bandit -r 01_security_sast.py -ll

Run tests:
    pip install pytest
    pytest 01_security_sast.py -v
"""

import hashlib
import os
import secrets
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest


# ─── A01 — Broken Access Control ──────────────────────────────────────────────

class ResourceAccess:
    """Demonstrates path traversal and access-control issues."""

    def __init__(self, base_dir: str):
        # Resolve to an absolute canonical path
        self._base = Path(base_dir).resolve()

    # INSECURE: Does not validate that the resolved path stays within base_dir
    def read_file_insecure(self, filename: str) -> str:
        path = self._base / filename
        return path.read_text()

    # SECURE: Validates that the resolved path stays within the base directory
    def read_file_secure(self, filename: str) -> str:
        # Resolve the path and check that it is inside self._base
        target = (self._base / filename).resolve()
        target.relative_to(self._base)  # raises ValueError if outside
        return target.read_text()


class TestResourceAccess:

    def test_secure_read_within_base_succeeds(self, tmp_path):
        (tmp_path / "safe.txt").write_text("safe content")
        accessor = ResourceAccess(str(tmp_path))
        assert accessor.read_file_secure("safe.txt") == "safe content"

    def test_secure_read_path_traversal_raises(self, tmp_path):
        accessor = ResourceAccess(str(tmp_path))
        with pytest.raises(ValueError):
            accessor.read_file_secure("../../etc/passwd")


# ─── A02 — Cryptographic Failures ─────────────────────────────────────────────

class PasswordHasher:
    """Demonstrates weak vs secure password hashing."""

    # INSECURE: MD5 is cryptographically broken (fast, no salt)
    @staticmethod
    def hash_insecure(password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()  # noqa: S324

    # SECURE: bcrypt / argon2 via the passlib library is preferred.
    # Here we use hashlib.scrypt (stdlib) as a demonstration.
    @staticmethod
    def hash_secure(password: str) -> bytes:
        salt = os.urandom(16)
        dk = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=2**14,   # CPU/memory cost (lower for tests, use 2**20 in prod)
            r=8,
            p=1,
            dklen=32,
        )
        return salt + dk  # store salt alongside the derived key

    @staticmethod
    def verify_secure(password: str, stored: bytes) -> bool:
        salt = stored[:16]
        stored_dk = stored[16:]
        dk = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )
        return secrets.compare_digest(dk, stored_dk)


class TestPasswordHasher:

    def test_secure_hash_round_trips(self):
        stored = PasswordHasher.hash_secure("my_secret_password")
        assert PasswordHasher.verify_secure("my_secret_password", stored)

    def test_secure_hash_wrong_password_fails(self):
        stored = PasswordHasher.hash_secure("correct_password")
        assert not PasswordHasher.verify_secure("wrong_password", stored)

    def test_two_hashes_of_same_password_differ(self):
        """Each hash uses a random salt — so they must differ."""
        h1 = PasswordHasher.hash_secure("password")
        h2 = PasswordHasher.hash_secure("password")
        assert h1 != h2


# ─── A03 — SQL Injection ──────────────────────────────────────────────────────

class UserDatabase:
    """Demonstrates SQL injection vulnerability and parameterised query fix."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE)"
        )
        self._conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'Alice', 'alice@example.com')")
        self._conn.commit()

    # INSECURE: Direct string interpolation allows SQL injection
    def find_by_email_insecure(self, email: str) -> list:
        query = f"SELECT * FROM users WHERE email = '{email}'"  # noqa: S608
        return self._conn.execute(query).fetchall()

    # SECURE: Parameterised query — user input is never concatenated into SQL
    def find_by_email_secure(self, email: str) -> list:
        return self._conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchall()


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


class TestUserDatabase:

    def test_secure_query_finds_user(self, db_conn):
        db = UserDatabase(db_conn)
        rows = db.find_by_email_secure("alice@example.com")
        assert len(rows) == 1
        assert rows[0][1] == "Alice"

    def test_secure_query_sql_injection_returns_empty(self, db_conn):
        """
        Classic SQL injection payload: ' OR '1'='1
        With parameterised queries this is treated as a literal string,
        so no rows are returned.
        """
        db = UserDatabase(db_conn)
        payload = "' OR '1'='1"
        rows = db.find_by_email_secure(payload)
        assert rows == [], "SQL injection should not return rows with parameterised queries"

    def test_insecure_query_sql_injection_returns_all_rows(self, db_conn):
        """
        Shows that the insecure version IS vulnerable — this test documents
        the problem so developers understand what they're fixing.
        """
        db = UserDatabase(db_conn)
        payload = "' OR '1'='1"
        rows = db.find_by_email_insecure(payload)
        # The injection succeeds and returns all rows
        assert len(rows) > 0, "Insecure query is vulnerable to SQL injection"


# ─── A07 — Authentication Failures ────────────────────────────────────────────

class TokenGenerator:
    """Demonstrates predictable vs cryptographically secure tokens."""

    # INSECURE: Predictable pseudo-random token
    @staticmethod
    def generate_insecure() -> str:
        import random  # noqa: PLC0415
        return str(random.randint(100000, 999999))  # noqa: S311

    # SECURE: Cryptographically secure random token
    @staticmethod
    def generate_secure(nbytes: int = 32) -> str:
        return secrets.token_hex(nbytes)


class TestTokenGenerator:

    def test_secure_token_has_expected_length(self):
        token = TokenGenerator.generate_secure(32)
        assert len(token) == 64  # hex: 2 chars per byte

    def test_secure_tokens_are_unique(self):
        tokens = {TokenGenerator.generate_secure() for _ in range(1000)}
        assert len(tokens) == 1000, "All tokens should be unique"
