"""
Level 3 - Advanced: BDD with pytest-bdd
=========================================
pytest-bdd allows you to write Gherkin feature files and bind
them to Python step definitions.

Prerequisites:
    pip install pytest pytest-bdd

Run:
    pytest 02_bdd_steps.py -v
"""

import pytest
from pytest_bdd import given, when, then, parsers, scenarios


# ─── Feature file reference ────────────────────────────────────────────────────
# Tells pytest-bdd which .feature file contains the scenarios to run.
scenarios("features/login.feature")


# ─── System Under Test ────────────────────────────────────────────────────────

class AuthService:
    """Simple authentication service used in BDD step definitions."""

    _users = {
        "alice@example.com": {"password": "secret123", "name": "Alice"},
        "bob@example.com":   {"password": "pass456",   "name": "Bob"},
    }

    def register(self, email: str, password: str, name: str) -> dict:
        self._users[email] = {"password": password, "name": name}
        return {"email": email, "name": name}

    def login(self, email: str, password: str) -> dict:
        user = self._users.get(email)
        if not user or user["password"] != password:
            raise PermissionError("Invalid credentials")
        return {"token": f"tok_{email}", "name": user["name"]}


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_service():
    return AuthService()


@pytest.fixture
def context():
    """Shared context dict for passing data between steps."""
    return {}


# ─── Step definitions ──────────────────────────────────────────────────────────

@given(parsers.parse('a registered user with email "{email}" and password "{password}"'))
def registered_user(auth_service, context, email, password):
    auth_service.register(email, password, name="Test User")
    context["email"] = email
    context["password"] = password
    context["auth_service"] = auth_service


@when("they log in with the correct password")
def login_with_correct_password(context):
    service = context["auth_service"]
    try:
        result = service.login(context["email"], context["password"])
        context["login_result"] = result
        context["error"] = None
    except PermissionError as e:
        context["login_result"] = None
        context["error"] = str(e)


@when(parsers.parse('they log in with the wrong password "{wrong_password}"'))
def login_with_wrong_password(context, wrong_password):
    service = context["auth_service"]
    try:
        result = service.login(context["email"], wrong_password)
        context["login_result"] = result
        context["error"] = None
    except PermissionError as e:
        context["login_result"] = None
        context["error"] = str(e)


@then("they should receive a valid auth token")
def should_receive_token(context):
    assert context["login_result"] is not None
    assert "token" in context["login_result"]
    assert context["login_result"]["token"].startswith("tok_")


@then("they should see an invalid credentials error")
def should_see_error(context):
    assert context["error"] is not None
    assert "Invalid credentials" in context["error"]


@then("they should not receive a token")
def should_not_receive_token(context):
    assert context["login_result"] is None
