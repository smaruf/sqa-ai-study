[← Level 1 — Basic](../level-1-basic/README.md) | [→ Level 3 — Advanced](../level-3-advanced/README.md)

# Level 2 — Intermediate: Integration Testing, Mocking & API Testing

Level 2 moves beyond isolated unit tests to cover **integration testing** patterns, **mocking/stubbing** external dependencies, and **API testing** with HTTP clients. These techniques are essential for verifying that components work together correctly without spinning up full production infrastructure.

---

## Key Concepts

### Integration Testing
Integration tests verify that **multiple components work correctly together**. Unlike unit tests, they may involve a real database, HTTP server, or message queue — or a realistic in-memory substitute.

**When to use:**
- Verifying that a service correctly reads/writes to a database
- Testing that two or more classes interact as intended
- Ensuring that a HTTP handler produces the right response

### Mocking and Stubbing

| Term | Meaning |
|------|---------|
| **Stub** | Returns predefined responses; does not verify calls |
| **Mock** | Verifies that specific calls were made (behaviour verification) |
| **Spy** | Wraps a real object; records interactions |
| **Fake** | A working but simplified implementation (e.g., in-memory DB) |

Mocking allows you to test a component that depends on external services (databases, APIs, email) without the real infrastructure.

### API Testing
API tests send real HTTP requests to a running service and verify the response status, headers, and body. They sit between unit tests and full E2E tests on the testing pyramid.

**Tools:**
- **Python**: `pytest` + `requests` + `pytest-flask` / `FastAPI TestClient`
- **Java**: REST Assured
- **Go**: `net/http/httptest`
- **C#**: `Microsoft.AspNetCore.Mvc.Testing` + `HttpClient`

---

## Examples in This Level

| File | Language | Topic |
|------|----------|-------|
| `python/01_mocking.py` | Python | `unittest.mock` — patching dependencies |
| `python/02_api_testing.py` | Python | FastAPI `TestClient` — HTTP endpoint tests |
| `java/EmailServiceTest.java` | Java | Mockito — mocking a mail sender |
| `java/UserApiTest.java` | Java | REST Assured — API tests against a Spring Boot app |
| `golang/email_service_test.go` | Go | Interface-based mocking (no library) |
| `golang/http_handler_test.go` | Go | `net/http/httptest` — HTTP handler tests |
| `csharp/EmailServiceTests.cs` | C# | Moq — mocking a mail sender |
| `csharp/UserApiTests.cs` | C# | `WebApplicationFactory` — in-process API tests |

---

## How to Run

### Python
```bash
pip install pytest pytest-mock httpx fastapi
cd level-2-intermediate/python
pytest -v
```

### Java
```bash
cd level-2-intermediate/java
mvn test
```

### Golang
```bash
cd level-2-intermediate/golang
go test -v ./...
```

### C\#
```bash
cd level-2-intermediate/csharp
dotnet test --verbosity normal
```

---

## Key Takeaways

1. **Mock at the boundary** — mock I/O (HTTP, DB, email), not pure business logic.
2. **Prefer fakes** over mocks when the interaction is complex — fakes are easier to maintain.
3. API tests should cover the happy path, error paths, and edge cases (invalid input, auth failures).
4. **Do not over-mock** — too many mocks make tests brittle and hard to understand.

---

[→ Next: Level 3 — Advanced](../level-3-advanced/README.md)
