[← Level 3 — Advanced](../level-3-advanced/README.md) | [→ Level 5 — Master](../level-5-master/README.md)

# Level 4 — Expert: Security Testing & Performance Testing

Level 4 covers two specialised and high-impact areas of SQA: **security testing** and **performance/load testing**. These practices protect your software against vulnerabilities and ensure it can handle real-world traffic.

---

## Security Testing

### The Security Testing Spectrum

| Technique | What it finds | When to run |
|-----------|--------------|-------------|
| **SAST** (Static Application Security Testing) | Insecure code patterns (SQL injection, hardcoded secrets, weak crypto) | On every commit / PR |
| **DAST** (Dynamic Application Security Testing) | Runtime vulnerabilities (XSS, CSRF, auth bypass) | Against running test/staging environment |
| **Dependency Scanning** | Known CVEs in third-party libraries | On every dependency change |
| **Secrets Scanning** | Accidentally committed credentials | On every commit |
| **Penetration Testing** | Complex attack chains | Periodically / before major releases |

### OWASP Top 10 (2021)
Every security-aware engineer should know the OWASP Top 10. The examples in this level demonstrate automated detection of several categories:

1. A01 — Broken Access Control
2. A02 — Cryptographic Failures
3. A03 — Injection (SQL, Command, LDAP)
4. A05 — Security Misconfiguration
5. A07 — Identification and Authentication Failures
6. A09 — Security Logging and Monitoring Failures

### Tools by Language

| Language | SAST | Dependency Scan | DAST |
|----------|------|----------------|------|
| Python | Bandit, Semgrep | Safety, pip-audit | OWASP ZAP |
| Java | SpotBugs + FindSecBugs, Semgrep | OWASP Dependency-Check | OWASP ZAP |
| Go | gosec, Semgrep | govulncheck | OWASP ZAP |
| C# | Security Code Scan, Roslyn Analysers | OWASP Dependency-Check | OWASP ZAP |

---

## Performance Testing

### Types of Performance Tests

| Type | Goal | Typical Question |
|------|------|-----------------|
| **Load test** | Verify behaviour under expected load | Can we handle 1000 concurrent users? |
| **Stress test** | Find the breaking point | At what point does the system fail? |
| **Spike test** | Verify recovery from sudden bursts | What happens when traffic doubles in 30 seconds? |
| **Soak / endurance test** | Find memory leaks and degradation | Does performance degrade over 24 hours? |
| **Volume test** | Verify large data volumes | Can we process 10 million records? |

### Tools by Language

| Language | Tool | Type |
|----------|------|------|
| Python | **Locust** | Load / stress / spike |
| Java | **Gatling** (Scala DSL) | Load / stress |
| Go | **k6** (JS scripts) | Load / performance |
| C# | **NBomber** | Load / stress / soak |

---

## Examples in This Level

| File | Language | Topic |
|------|----------|-------|
| `python/01_security_sast.py` | Python | Bandit-flagged anti-patterns + secure alternatives |
| `python/02_performance_locust.py` | Python | Locust load test for a FastAPI service |
| `java/SecurityAntiPatternsTest.java` | Java | SAST-detectable issues (SQL injection, weak hash) |
| `java/GatlingSimulation.scala` | Java/Scala | Gatling HTTP load simulation |
| `golang/security_test.go` | Go | gosec-flagged patterns + secure alternatives |
| `golang/k6_script.js` | Go/k6 | k6 load test script |
| `csharp/SecurityTests.cs` | C# | Security Code Scan anti-patterns |
| `csharp/NBomberLoadTest.cs` | C# | NBomber load test scenario |

---

## How to Run

### Python — Security (Bandit)
```bash
pip install bandit
bandit -r level-4-expert/python -ll
```

### Python — Load Test (Locust)
```bash
pip install locust fastapi uvicorn
# Start the app first: uvicorn app:app &
locust -f level-4-expert/python/02_performance_locust.py --headless \
       --users 50 --spawn-rate 10 --run-time 60s --host http://localhost:8000
```

### Go — Security (govulncheck + gosec)
```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec level-4-expert/golang/...
```

### C\# — Load Test (NBomber)
```bash
cd level-4-expert/csharp
dotnet run --project LoadTest.csproj
```

---

## Key Takeaways

1. **Shift security left** — run SAST and dependency scanning on every commit, not only before release.
2. **Never test with production credentials** — use separate test tokens/environments.
3. **Define performance budgets** — specify acceptable p95 latency and error rates before starting a load test.
4. **Test incrementally** — start with a small number of virtual users and increase gradually.
5. **Security tests complement, not replace, security reviews** — automated tools miss logic flaws.

---

[→ Next: Level 5 — Master](../level-5-master/README.md)
