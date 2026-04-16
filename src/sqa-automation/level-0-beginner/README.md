[← SQA Automation](../README.md) | [→ Level 1 — Basic](../level-1-basic/README.md)

# Level 0 — Beginner: SQA Fundamentals

Welcome to Level 0! Before writing a single line of test code, it is essential to understand *why* we test, *what* we test, and *how* a test is structured. This level introduces core SQA concepts and walks you through your very first test in each of the four languages.

---

## Core Concepts

### What is SQA?
Software Quality Assurance (SQA) is a systematic process that ensures a software product meets defined quality standards before it reaches users. SQA covers planning, monitoring, and controlling software development processes.

### The Testing Pyramid

```
          /\
         /E2E\          ← few, slow, expensive
        /------\
       / Integr \       ← medium number
      /----------\
     /   Unit     \     ← many, fast, cheap
    /______________\
```

The pyramid recommends investing most effort in fast, focused **unit tests**, supported by a smaller number of **integration tests**, with a thin layer of **end-to-end tests** at the top.

### Types of Testing

| Type | Scope | Speed | Cost |
|------|-------|-------|------|
| Unit | Single function / class | Very fast | Low |
| Integration | Multiple components | Fast–Medium | Medium |
| System / E2E | Entire application | Slow | High |
| Acceptance (UAT) | Business requirements | Slow | High |
| Security | Vulnerabilities & weaknesses | Varies | Medium–High |
| Performance | Speed, throughput, stability | Medium | Medium |

### Anatomy of a Test: Arrange–Act–Assert (AAA)

Every well-written test follows three steps:

```
Arrange  →  set up the system under test and its inputs
Act      →  call the function / trigger the behaviour
Assert   →  verify the outcome matches expectations
```

### What Makes a Good Test?

A good test is:
- **Fast** — runs in milliseconds
- **Isolated** — does not depend on external services or other tests
- **Repeatable** — gives the same result every time
- **Self-documenting** — clearly states what it tests
- **Failing for the right reason** — fails when the code is wrong, passes when it is correct

---

## Examples in This Level

| File | Language | Topic |
|------|----------|-------|
| `python/01_first_test.py` | Python | First pytest test — calculator functions |
| `python/02_test_anatomy.py` | Python | AAA pattern, naming conventions |
| `java/CalculatorTest.java` | Java | First JUnit 5 test |
| `java/TestAnatomyTest.java` | Java | AAA pattern in Java |
| `golang/calculator_test.go` | Go | First Go test with the standard library |
| `golang/anatomy_test.go` | Go | AAA pattern in Go |
| `csharp/CalculatorTests.cs` | C# | First NUnit test |
| `csharp/TestAnatomyTests.cs` | C# | AAA pattern in C# |

---

## How to Run

### Python
```bash
pip install pytest
cd level-0-beginner/python
pytest -v
```

### Java
```bash
cd level-0-beginner/java
mvn test          # or: gradle test
```

### Golang
```bash
cd level-0-beginner/golang
go test -v ./...
```

### C\#
```bash
cd level-0-beginner/csharp
dotnet test --verbosity normal
```

---

## Key Takeaways

1. Tests are code — treat them with the same care as production code.
2. A failing test that you wrote correctly is a success: it found a bug.
3. Start with the simplest possible test and build up from there.
4. The AAA pattern keeps tests readable and maintainable.

---

[→ Next: Level 1 — Basic Unit Testing](../level-1-basic/README.md)
