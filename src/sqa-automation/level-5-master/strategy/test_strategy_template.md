# Test Strategy Document Template

> **Instructions:** Copy this template for each project. Fill in the `[...]` placeholders. Review with the team at the start of each major release cycle.

---

## 1. Project Overview

| Field | Value |
|-------|-------|
| Project name | [Project name] |
| Version / release | [1.0 / Q1 2025] |
| Author | [Name, role] |
| Date | [YYYY-MM-DD] |
| Review date | [YYYY-MM-DD] |

---

## 2. Scope

### In Scope
- [List of features, modules, APIs, or user journeys covered by this strategy]

### Out of Scope
- [Items explicitly excluded and why]

---

## 3. Quality Objectives

| Objective | Metric | Target |
|-----------|--------|--------|
| Correctness | Bug escape rate | < 1 bug per 1000 story points |
| Reliability | Uptime | 99.9% |
| Performance | p95 API latency | < 500 ms |
| Security | Critical CVEs | 0 |
| Accessibility | WCAG level | AA |

---

## 4. Risk-Based Prioritisation

Identify the areas of highest risk and ensure they receive the most test coverage.

| Area / Feature | Risk Level | Reason | Test Priority |
|----------------|-----------|--------|---------------|
| Authentication & authorisation | High | Security-critical | P0 |
| Payment processing | High | Financial impact | P0 |
| User data storage | High | GDPR / privacy | P0 |
| [Feature X] | Medium | [Reason] | P1 |
| [Feature Y] | Low | [Reason] | P2 |

---

## 5. Test Types and Coverage Targets

| Test Type | Framework(s) | Coverage Target | When Run |
|-----------|-------------|----------------|----------|
| Unit | pytest / JUnit / go test / NUnit | ≥ 85% branch | Every PR |
| Integration | pytest / REST Assured / httptest | Key integration paths | Every PR |
| Contract | Pact | All consumer/provider pairs | Every PR |
| E2E / Acceptance | Playwright / Selenium | Critical user journeys | Merge to main |
| Security (SAST) | Bandit / gosec / Security Code Scan | 0 high findings | Every PR |
| Security (DAST) | OWASP ZAP | 0 high/critical findings | Weekly |
| Dependency scan | Safety / govulncheck / OWASP DC | 0 critical CVEs | Daily |
| Performance | Locust / k6 / Gatling / NBomber | p95 < 500ms, errors < 1% | Pre-release |
| Accessibility | axe-core / Lighthouse | WCAG AA | Every PR |
| Mutation | mutmut / PITest / gremlins / Stryker | Kill rate ≥ 80% | Weekly |

---

## 6. Test Environments

| Environment | Purpose | Data | Who Manages |
|-------------|---------|------|-------------|
| local | Developer testing | Seeded fake data | Developer |
| CI | Automated tests on PRs | Ephemeral test data | CI/CD pipeline |
| staging | Integration & E2E | Anonymised production snapshot | DevOps |
| performance | Load & stress tests | Synthetic data | QA / DevOps |
| production | Synthetic monitoring | Real users (read-only) | SRE |

---

## 7. Test Data Strategy

- Unit tests: inline fixtures and factory functions
- Integration tests: in-memory databases (H2, SQLite, testcontainers)
- E2E tests: seeded test accounts; cleaned up after each run
- Performance tests: generated synthetic data (avoid using production PII)
- Secrets: managed via vault / CI secret store; never committed to source

---

## 8. CI/CD Gates

| Stage | Gate | Failure Action |
|-------|------|----------------|
| Pull Request | All unit + integration tests pass | Block merge |
| Pull Request | Code coverage ≥ target | Block merge |
| Pull Request | 0 SAST high/critical findings | Block merge |
| Merge to main | All E2E tests pass | Block deploy |
| Pre-release | Performance budget met | Block release |
| Pre-release | 0 open critical CVEs | Block release |

---

## 9. Roles and Responsibilities

| Responsibility | Owner |
|----------------|-------|
| Test strategy design | QA Lead |
| Unit test authorship | Developer |
| E2E test authorship | QA Engineer |
| Security scanning setup | Security / DevSecOps |
| Performance test design | Performance Engineer / QA |
| CI/CD pipeline | DevOps / Platform |
| Test report review | QA Lead + Engineering Manager |

---

## 10. Defect Management

| Severity | Definition | SLA (time to fix) |
|----------|-----------|-------------------|
| P0 — Critical | Data loss, security breach, complete outage | Same day |
| P1 — High | Major feature broken, workaround unavailable | Next sprint |
| P2 — Medium | Feature degraded, workaround exists | Backlog grooming |
| P3 — Low | Minor visual / UX issue | Backlog |

---

## 11. Reporting

| Report | Frequency | Audience | Tool |
|--------|-----------|----------|------|
| Test run summary | Per PR | Developer | GitHub PR check |
| Coverage report | Per PR | Developer, QA | Codecov / SonarQube |
| Security scan report | Per PR + daily | Security, QA Lead | GitHub Security tab |
| Performance test report | Per run | QA, Perf Lead, EM | Locust / Gatling HTML |
| Quality dashboard | Weekly | EM, Product | SonarQube / Datadog |

---

## 12. Test Automation Approach

### Do Automate
- Regression tests for all fixed bugs
- Happy-path and critical negative scenarios
- All security and dependency scans
- Performance baseline validation

### Do Not Automate (at this time)
- One-off exploratory testing
- Tests with extremely high maintenance cost relative to value
- Tests that require human aesthetic judgment

---

## 13. Tools Summary

| Language | Unit | API | E2E | Security | Performance |
|----------|------|-----|-----|----------|-------------|
| Python | pytest | FastAPI TestClient | Playwright | Bandit, Safety | Locust |
| Java | JUnit 5, AssertJ | REST Assured | Playwright | OWASP DC, SpotBugs | Gatling |
| Go | testing, testify | net/http/httptest | Playwright-go | gosec, govulncheck | k6 |
| C# | NUnit, xUnit | WebApplicationFactory | Playwright .NET | Security Code Scan | NBomber |

---

## 14. Review and Update

This document should be reviewed:
- At the start of each release cycle
- When new technology is adopted
- After a major production incident
- When the team structure changes

---

*Template version 1.0 — SQA Automation Learning Path, Level 5 Master*
