[← Back to Main Repository](../../README.md)

# SQA Automation — Zero to Expert

A comprehensive, multi-language learning path for **Software Quality Assurance (SQA) Automation**. This guide takes you from first principles to expert-level practices — including functional, integration, end-to-end, security, and performance testing — across four languages: **Python**, **Java**, **Golang**, and **C#**.

---

## Table of Contents

- [Introduction](#introduction)
- [Learning Path](#learning-path)
- [Technologies Covered](#technologies-covered)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Learning Levels](#learning-levels)
- [Prerequisites](#prerequisites)
- [Contributing](#contributing)

---

## Introduction

Software Quality Assurance is not just about finding bugs — it is a discipline that ensures software systems meet defined standards of quality, security, and performance. This project gives you hands-on practice through six progressive levels, each building on the last. Every level provides working examples in all four languages so you can apply the concepts in your preferred stack.

---

## Learning Path

| Level | Name | Focus |
|-------|------|--------|
| [Level 0](level-0-beginner/README.md) | Beginner | SQA concepts, test anatomy, first test in each language |
| [Level 1](level-1-basic/README.md) | Basic | Unit testing frameworks, assertions, test organisation |
| [Level 2](level-2-intermediate/README.md) | Intermediate | Integration testing, mocking, API testing |
| [Level 3](level-3-advanced/README.md) | Advanced | End-to-end testing, BDD, CI/CD integration |
| [Level 4](level-4-expert/README.md) | Expert | Security testing, performance & load testing |
| [Level 5](level-5-master/README.md) | Master | Full test strategy, AI-assisted testing, observability |

---

## Technologies Covered

### Python
- **pytest** — unit and integration testing
- **unittest.mock** — mocking and stubbing
- **requests / httpx** — API testing
- **Playwright / Selenium** — browser automation
- **Behave / pytest-bdd** — BDD
- **Bandit / Safety** — security static analysis
- **Locust** — performance / load testing

### Java
- **JUnit 5** — unit testing
- **Mockito** — mocking
- **REST Assured** — API testing
- **Selenium / Playwright** — browser automation
- **Cucumber** — BDD
- **SpotBugs / OWASP Dependency-Check** — security analysis
- **Gatling / JMeter** — performance testing

### Golang
- **testing** (stdlib) — unit testing
- **testify** — assertions and mocking
- **net/http/httptest** — HTTP handler testing
- **Playwright-go** — browser automation
- **Godog** — BDD (Cucumber for Go)
- **gosec** — security static analysis
- **k6** — performance testing

### C\#
- **NUnit / xUnit** — unit testing
- **Moq** — mocking
- **RestSharp / HttpClient** — API testing
- **Playwright for .NET** — browser automation
- **SpecFlow** — BDD
- **Security Code Scan / OWASP ZAP** — security testing
- **NBomber** — performance / load testing

---

## Directory Structure

```
sqa-automation/
├── README.md
├── level-0-beginner/
│   ├── README.md
│   ├── python/
│   ├── java/
│   ├── golang/
│   └── csharp/
├── level-1-basic/
│   ├── README.md
│   ├── python/
│   ├── java/
│   ├── golang/
│   └── csharp/
├── level-2-intermediate/
│   ├── README.md
│   ├── python/
│   ├── java/
│   ├── golang/
│   └── csharp/
├── level-3-advanced/
│   ├── README.md
│   ├── python/
│   ├── java/
│   ├── golang/
│   └── csharp/
├── level-4-expert/
│   ├── README.md
│   ├── python/
│   ├── java/
│   ├── golang/
│   └── csharp/
└── level-5-master/
    ├── README.md
    ├── python/
    ├── java/
    ├── golang/
    └── csharp/
```

---

## Getting Started

### Python
```bash
pip install pytest pytest-cov pytest-mock requests locust bandit
cd src/sqa-automation/level-0-beginner/python
pytest -v
```

### Java
```bash
# Requires JDK 17+ and Maven
cd src/sqa-automation/level-0-beginner/java
mvn test
```

### Golang
```bash
# Requires Go 1.21+
cd src/sqa-automation/level-0-beginner/golang
go test ./...
```

### C\#
```bash
# Requires .NET 8 SDK
cd src/sqa-automation/level-0-beginner/csharp
dotnet test
```

---

## Learning Levels

### [Level 0 — Beginner](level-0-beginner/README.md)
- What is SQA? Roles, responsibilities, and the testing pyramid
- Types of testing: unit, integration, system, acceptance
- Anatomy of a test: Arrange-Act-Assert (AAA)
- Writing your first test in each language

### [Level 1 — Basic](level-1-basic/README.md)
- Unit testing frameworks and test runners
- Test organisation: suites, fixtures, setup/teardown
- Assertions, matchers, and custom messages
- Code coverage measurement
- Parameterised / data-driven tests

### [Level 2 — Intermediate](level-2-intermediate/README.md)
- Integration testing patterns
- Mocking, stubbing, and faking dependencies
- API testing with HTTP clients
- Database testing strategies
- Test data management

### [Level 3 — Advanced](level-3-advanced/README.md)
- End-to-end (E2E) browser automation
- Behaviour-Driven Development (BDD)
- Contract testing with Pact
- CI/CD pipeline integration
- Test reporting and dashboards

### [Level 4 — Expert](level-4-expert/README.md)
- Security testing: SAST, DAST, and dependency scanning
- OWASP Top 10 coverage in automated tests
- Performance and load testing
- Chaos engineering basics
- Shift-left security practices

### [Level 5 — Master](level-5-master/README.md)
- Full test strategy and architecture design
- AI-assisted test generation
- Mutation testing
- Observability: tracing, metrics, and alerting for tests
- Building a quality engineering culture

---

## Prerequisites

| Level | Requirements |
|-------|-------------|
| 0–1 | Basic programming in at least one language |
| 2–3 | Familiarity with REST APIs and HTTP |
| 4 | Understanding of software architecture and deployment |
| 5 | Experience shipping production software |

---

## Contributing

Contributions are welcome! Please follow the existing patterns:
- Each example should be runnable as-is
- Include comments explaining *why*, not just *what*
- Keep examples focused on a single concept per file
- Update the relevant README when adding new examples

See the main [Contribution Guidelines](../../README.md#contribution-guidelines) for more details.
