[← Level 4 — Expert](../level-4-expert/README.md) | [← Back to SQA Automation](../README.md)

# Level 5 — Master: Full Test Strategy, AI-Assisted Testing & Observability

Level 5 is about thinking at a systems level. Expert practitioners do not just write tests — they design **quality strategies**, leverage **AI and automation** to scale their efforts, and ensure that quality is **observable in production**.

---

## Key Concepts

### Test Strategy Design

A test strategy answers:
1. **What** are we testing? (scope, risk areas, SLAs)
2. **How** are we testing? (test types, tools, frameworks)
3. **When** are we testing? (shift-left, gates, automated triggers)
4. **Who** is responsible? (ownership model, RACI)
5. **How do we know it's enough?** (coverage targets, quality metrics)

#### The Testing Quadrants (Brian Marick)

```
                │ Supporting the Team │  Critiquing the Product
                │                     │
Technology-     │  Q1: Unit, Component │  Q3: Exploratory, Usability,
facing          │  Integration, API    │  Acceptance
                │                     │
Business-       │  Q2: Functional,     │  Q4: Performance, Load,
facing          │  Story, BDD          │  Security, Chaos
```

### Mutation Testing
Mutation testing verifies that your tests actually *catch* bugs by:
1. Introducing small artificial faults (mutants) into the code
2. Running the tests
3. Checking if the tests detect (kill) each mutant

A high mutation kill rate indicates that your tests are meaningful.

**Tools:**
- **Python** — mutmut, mutpy
- **Java** — PITest (PIT)
- **Go** — gremlins
- **C#** — Stryker.NET

### AI-Assisted Testing
Modern AI tools accelerate test creation and maintenance:
- **GitHub Copilot** — auto-complete test cases as you type
- **CodiumAI / Pynguin** — generate test suites from source code
- **Diffblue Cover** — AI-generated Java unit tests
- **GPT-based prompting** — generate test plans, edge cases, and test data

### Observability for Quality
Production quality is monitored, not just tested:
- **Distributed tracing** (OpenTelemetry) — trace requests end-to-end
- **Error tracking** (Sentry, Rollbar) — capture and group production errors
- **SLI/SLO/SLA** — define and track Service Level Indicators/Objectives
- **Synthetic monitoring** — run E2E tests continuously in production

### Chaos Engineering
Proactively discover weaknesses by injecting failures in controlled conditions:
- Kill a container randomly
- Introduce network latency
- Exhaust memory or CPU
- Simulate cloud zone outages

**Tools:** Chaos Monkey, LitmusChaos, k6 Fault Injection

---

## Examples in This Level

| File | Language | Topic |
|------|----------|-------|
| `python/01_mutation_testing.py` | Python | Writing mutation-resistant tests |
| `python/02_property_based.py` | Python | Property-based testing with Hypothesis |
| `python/03_observability.py` | Python | OpenTelemetry tracing in tests |
| `java/MutationResistantTest.java` | Java | PITest-compatible tests |
| `java/PropertyBasedTest.java` | Java | QuickCheck-style property tests |
| `golang/property_test.go` | Go | Rapid (property-based testing for Go) |
| `golang/mutation_test.go` | Go | Gremlins-compatible mutation-resistant tests |
| `csharp/MutationResistantTests.cs` | C# | Stryker.NET-compatible tests |
| `csharp/PropertyBasedTests.cs` | C# | FsCheck property-based tests |
| `strategy/test_strategy_template.md` | All | Reusable test strategy document template |

---

## Test Strategy Template

See [`strategy/test_strategy_template.md`](strategy/test_strategy_template.md) for a reusable template covering:
- Scope and objectives
- Risk-based test prioritisation
- Tooling decisions
- Coverage targets
- CI/CD gates
- Reporting and ownership

---

## How to Run

### Python — Property-based tests (Hypothesis)
```bash
pip install pytest hypothesis
cd level-5-master/python
pytest 02_property_based.py -v --hypothesis-show-statistics
```

### Python — Mutation testing (mutmut)
```bash
pip install mutmut
mutmut run --paths-to-mutate level-5-master/python/
mutmut results
```

### Java — PITest (mutation testing)
```bash
cd level-5-master/java
mvn org.pitest:pitest-maven:mutationCoverage
# Report: target/pit-reports/*/index.html
```

### Go — Property-based tests (rapid)
```bash
cd level-5-master/golang
go get pgregory.net/rapid
go test -v ./...
```

### C\# — Stryker.NET (mutation testing)
```bash
dotnet tool install -g dotnet-stryker
cd level-5-master/csharp
dotnet stryker
```

---

## Quality Metrics Dashboard

Track these metrics over time:

| Metric | Target | Tooling |
|--------|--------|---------|
| Mutation score | > 80% | PITest, Stryker.NET, mutmut |
| Branch coverage | > 85% | JaCoCo, pytest-cov, coverlet |
| DAST findings | 0 high/critical | OWASP ZAP |
| Dependency CVEs | 0 critical | OWASP DC, Safety, govulncheck |
| p95 response time | < 500ms | Locust, Gatling, k6 |
| Error rate (prod) | < 0.1% | Sentry, Datadog |
| MTTR | < 30 min | PagerDuty, Opsgenie |

---

## Key Takeaways

1. Quality is a team sport — cultivate a quality engineering culture, not a QA gatekeeping culture.
2. Shift security and performance left — the earlier you find issues, the cheaper they are to fix.
3. AI tools augment, not replace, human judgement about what to test.
4. Observability in production is the last line of defence — instrument everything.
5. Continuous improvement: track metrics over time and celebrate when they improve.

---

[← Back to SQA Automation Overview](../README.md)
