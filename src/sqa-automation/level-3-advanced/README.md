[← Level 2 — Intermediate](../level-2-intermediate/README.md) | [→ Level 4 — Expert](../level-4-expert/README.md)

# Level 3 — Advanced: End-to-End Testing, BDD & CI/CD Integration

Level 3 covers the top of the testing pyramid: **end-to-end (E2E) testing** that exercises the entire application, **Behaviour-Driven Development (BDD)** for expressing requirements as executable specifications, and integrating tests into **CI/CD pipelines**.

---

## Key Concepts

### End-to-End (E2E) Testing
E2E tests verify the system as a whole from the user's perspective, often driving a real browser or sending requests through the full HTTP stack.

**When to use:**
- Verifying critical user journeys (login, checkout, form submission)
- Smoke tests after deployments
- Regression tests for known user-facing bugs

**Tools:**
- **Playwright** — fast, cross-browser, supports Python/Java/Go/C#
- **Selenium WebDriver** — widely used, large ecosystem
- **Cypress** — JavaScript/TypeScript-first, great DX

### Behaviour-Driven Development (BDD)
BDD uses structured natural-language specifications (Gherkin) that serve as both documentation and automated tests.

```gherkin
Feature: User login

  Scenario: Successful login with valid credentials
    Given a registered user with email "alice@example.com"
    When they log in with the correct password
    Then they should see their dashboard
    And they should receive a welcome message
```

**Frameworks:**
- **Python** — Behave, pytest-bdd
- **Java** — Cucumber
- **Go** — Godog
- **C#** — SpecFlow

### CI/CD Integration
Tests only protect you if they run automatically. Key practices:
- Run unit/integration tests on every pull request
- Run E2E tests on merges to main/staging
- Fail the build fast — run the fastest tests first
- Publish test reports as CI artifacts

---

## Examples in This Level

| File | Language | Topic |
|------|----------|-------|
| `python/01_playwright_e2e.py` | Python | Playwright browser automation |
| `python/02_bdd_steps.py` | Python | pytest-bdd step definitions |
| `python/features/login.feature` | Gherkin | BDD feature file |
| `java/LoginE2ETest.java` | Java | Playwright for Java |
| `java/LoginSteps.java` | Java | Cucumber step definitions |
| `java/features/login.feature` | Gherkin | BDD feature file |
| `golang/e2e_test.go` | Go | Playwright-go browser test |
| `golang/login_steps_test.go` | Go | Godog step definitions |
| `golang/features/login.feature` | Gherkin | BDD feature file |
| `csharp/LoginE2ETests.cs` | C# | Playwright for .NET |
| `csharp/LoginSteps.cs` | C# | SpecFlow step definitions |
| `csharp/Features/Login.feature` | Gherkin | BDD feature file |
| `ci/github-actions.yml` | YAML | Example GitHub Actions pipeline |

---

## How to Run

### Python (pytest-bdd)
```bash
pip install pytest pytest-bdd playwright
playwright install chromium
cd level-3-advanced/python
pytest -v
```

### Java (Cucumber + Playwright)
```bash
cd level-3-advanced/java
mvn test
```

### Golang (Godog + Playwright-go)
```bash
cd level-3-advanced/golang
go test -v ./...
```

### C\# (SpecFlow + Playwright)
```bash
cd level-3-advanced/csharp
dotnet test --verbosity normal
```

---

## CI/CD Pipeline Pattern

```yaml
# .github/workflows/test.yml
jobs:
  unit:          # Runs on every push/PR — fast feedback
    runs-on: ubuntu-latest
    steps: [checkout, setup, run unit tests]

  integration:   # Runs after unit tests pass
    needs: unit
    steps: [checkout, setup, start services, run integration tests]

  e2e:           # Runs on merge to main
    needs: integration
    steps: [checkout, setup, deploy to staging, run E2E tests]
```

---

## Key Takeaways

1. E2E tests are valuable but expensive — keep them focused on critical paths.
2. BDD works best when business stakeholders help write the feature files.
3. CI/CD should run tests in parallel where possible to keep feedback fast.
4. Always upload test reports as CI artifacts so failures are easy to investigate.

---

[→ Next: Level 4 — Expert](../level-4-expert/README.md)
