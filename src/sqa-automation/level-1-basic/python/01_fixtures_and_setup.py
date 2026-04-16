"""
Level 1 - Basic: pytest Fixtures, Setup, and Teardown
======================================================
Fixtures are pytest's primary mechanism for sharing reusable setup
between tests. They are injected as function parameters — no inheritance
or setUp() naming convention needed.

Run:
    pytest 01_fixtures_and_setup.py -v
"""

import pytest


# ─── System Under Test ────────────────────────────────────────────────────────

class UserRepository:
    """In-memory user store — stands in for a real database."""

    def __init__(self):
        self._store: dict[int, dict] = {}
        self._next_id = 1

    def create(self, name: str, email: str) -> dict:
        user = {"id": self._next_id, "name": name, "email": email}
        self._store[self._next_id] = user
        self._next_id += 1
        return user

    def find_by_id(self, user_id: int) -> dict | None:
        return self._store.get(user_id)

    def find_by_email(self, email: str) -> dict | None:
        return next((u for u in self._store.values() if u["email"] == email), None)

    def delete(self, user_id: int) -> bool:
        return self._store.pop(user_id, None) is not None

    def count(self) -> int:
        return len(self._store)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def repo():
    """Provide a fresh, empty UserRepository for each test."""
    return UserRepository()


@pytest.fixture
def populated_repo(repo):
    """Provide a UserRepository pre-loaded with two users.

    Fixtures can depend on other fixtures — pytest resolves the graph.
    """
    repo.create("Alice", "alice@example.com")
    repo.create("Bob",   "bob@example.com")
    return repo


@pytest.fixture(autouse=False)
def log_test_name(request):
    """Optional fixture that logs the test name before/after each test.

    The 'yield' separates setup (before) from teardown (after).
    """
    print(f"\n▶ starting: {request.node.name}")
    yield
    print(f"✔ finished: {request.node.name}")


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestUserRepositoryCreate:

    def test_create_returns_user_with_id(self, repo):
        user = repo.create("Alice", "alice@example.com")
        assert user["id"] == 1
        assert user["name"] == "Alice"
        assert user["email"] == "alice@example.com"

    def test_create_increments_id(self, repo):
        first  = repo.create("Alice", "alice@example.com")
        second = repo.create("Bob",   "bob@example.com")
        assert second["id"] == first["id"] + 1

    def test_count_increases_after_create(self, repo):
        assert repo.count() == 0
        repo.create("Alice", "alice@example.com")
        assert repo.count() == 1


class TestUserRepositoryFind:

    def test_find_by_id_returns_correct_user(self, populated_repo):
        user = populated_repo.find_by_id(1)
        assert user is not None
        assert user["name"] == "Alice"

    def test_find_by_id_returns_none_for_unknown_id(self, populated_repo):
        assert populated_repo.find_by_id(999) is None

    def test_find_by_email_returns_correct_user(self, populated_repo):
        user = populated_repo.find_by_email("bob@example.com")
        assert user is not None
        assert user["name"] == "Bob"

    def test_find_by_email_returns_none_for_unknown_email(self, populated_repo):
        assert populated_repo.find_by_email("unknown@example.com") is None


class TestUserRepositoryDelete:

    def test_delete_existing_user_returns_true(self, populated_repo):
        result = populated_repo.delete(1)
        assert result is True
        assert populated_repo.find_by_id(1) is None

    def test_delete_decrements_count(self, populated_repo):
        before = populated_repo.count()
        populated_repo.delete(1)
        assert populated_repo.count() == before - 1

    def test_delete_nonexistent_user_returns_false(self, repo):
        assert repo.delete(999) is False
