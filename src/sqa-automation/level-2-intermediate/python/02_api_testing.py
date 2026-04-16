"""
Level 2 - Intermediate: API Testing with FastAPI TestClient
===========================================================
FastAPI's TestClient (backed by httpx) lets you send HTTP requests
directly to your app in-process — no network required.

Run:
    pip install pytest fastapi httpx
    pytest 02_api_testing.py -v
"""

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr
from typing import Optional


# ─── Application ──────────────────────────────────────────────────────────────

app = FastAPI(title="User API")

# In-memory store (acts as a fake database for tests)
_users: dict[int, dict] = {}
_next_id = 1


class CreateUserRequest(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUserRequest):
    global _next_id
    if "@" not in payload.email:
        raise HTTPException(status_code=422, detail="Invalid email address")
    user = {"id": _next_id, "name": payload.name, "email": payload.email}
    _users[_next_id] = user
    _next_id += 1
    return user


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = _users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users", response_model=list[UserResponse])
def list_users():
    return list(_users.values())


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    if user_id not in _users:
        raise HTTPException(status_code=404, detail="User not found")
    del _users[user_id]


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_store():
    """Clear the in-memory store before each test for test isolation."""
    global _users, _next_id
    _users = {}
    _next_id = 1
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestCreateUser:

    def test_create_user_returns_201(self, client):
        response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        assert response.status_code == 201

    def test_create_user_returns_correct_body(self, client):
        response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        body = response.json()
        assert body["id"] == 1
        assert body["name"] == "Alice"
        assert body["email"] == "alice@example.com"

    def test_create_user_invalid_email_returns_422(self, client):
        response = client.post("/users", json={"name": "Alice", "email": "not-an-email"})
        assert response.status_code == 422

    def test_create_user_missing_name_returns_422(self, client):
        response = client.post("/users", json={"email": "alice@example.com"})
        assert response.status_code == 422


class TestGetUser:

    def test_get_existing_user_returns_200(self, client):
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        response = client.get("/users/1")
        assert response.status_code == 200
        assert response.json()["name"] == "Alice"

    def test_get_nonexistent_user_returns_404(self, client):
        response = client.get("/users/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"


class TestListUsers:

    def test_list_returns_empty_array_when_no_users(self, client):
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_all_created_users(self, client):
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        client.post("/users", json={"name": "Bob",   "email": "bob@example.com"})

        response = client.get("/users")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestDeleteUser:

    def test_delete_existing_user_returns_204(self, client):
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        response = client.delete("/users/1")
        assert response.status_code == 204

    def test_delete_removes_user_from_list(self, client):
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        client.delete("/users/1")

        response = client.get("/users")
        assert response.json() == []

    def test_delete_nonexistent_user_returns_404(self, client):
        response = client.delete("/users/999")
        assert response.status_code == 404
