# SQA AI Study Repository

A multi-language **Software Quality Assurance (SQA) automation** study repository with a full phased learning path in **Python**, **Java**, **Golang**, and **C#**, progressing from zero to expert level across unit, integration, API, end-to-end, security, and performance testing.

## 📁 Repository Structure

```
sqa-ai-study/
├── src/
│   ├── sqa-automation/        # SQA automation learning path (6 levels)
│   │   ├── level-0-beginner/
│   │   ├── level-1-basic/
│   │   ├── level-2-intermediate/
│   │   ├── level-3-advanced/
│   │   ├── level-4-expert/
│   │   └── level-5-master/
│   └── local-llm-for-sqa/    # Run local LLMs (Ollama + Qwen3) for SQA tasks
│       ├── README.md
│       └── python/
```

## 🚀 SQA Automation — Zero to Expert

### [SQA Automation Learning Path](./src/sqa-automation/README.md)

A comprehensive, multi-language SQA automation guide covering 6 progressive levels — from writing your first test to full test strategy, AI-assisted testing, security testing, and performance testing.

| Level | Name | Focus |
|-------|------|--------|
| [Level 0](./src/sqa-automation/level-0-beginner/README.md) | Beginner | SQA concepts, test anatomy, first test in each language |
| [Level 1](./src/sqa-automation/level-1-basic/README.md) | Basic | Unit testing frameworks, assertions, test organisation |
| [Level 2](./src/sqa-automation/level-2-intermediate/README.md) | Intermediate | Integration testing, mocking, API testing |
| [Level 3](./src/sqa-automation/level-3-advanced/README.md) | Advanced | End-to-end testing, BDD, CI/CD integration |
| [Level 4](./src/sqa-automation/level-4-expert/README.md) | Expert | Security testing, performance & load testing |
| [Level 5](./src/sqa-automation/level-5-master/README.md) | Master | Full test strategy, AI-assisted testing, observability |

---

## 🤖 Local LLM for SQA

### [Local LLM for SQA](./src/local-llm-for-sqa/README.md)

Run AI models **privately on your laptop** using [Ollama](https://ollama.com/) and apply them to everyday SQA tasks — test case generation, bug triage, test data creation, and more. No cloud account, no cost, no data leaving your machine.

Focused on [**Qwen3**](https://github.com/QwenLM/Qwen3) — the recommended open-weight model for SQA work — with its unique **thinking mode** that produces auditable chain-of-thought reasoning before every answer.

| File | Topic |
|------|-------|
| `python/01_llm_client.py` | Ollama HTTP client with contract tests |
| `python/02_test_case_generator.py` | Test case generation with schema validation |
| `python/03_bug_triage.py` | Bug severity classification with consistency gates |
| `python/04_test_data_factory.py` | Test data generation with PII guards |
| `python/05_prompt_safety.py` | Prompt injection prevention (OWASP LLM01) |
| `python/06_qwen3_thinking_mode.py` | Qwen3 thinking/non-thinking modes for SQA |

```bash
# Run all unit tests (no Ollama needed — fully mocked)
pip install pytest pytest-mock requests
cd src/local-llm-for-sqa
pytest -m "not integration" -v
```

## 🛠️ Getting Started

### Python
```bash
pip install pytest pytest-cov pytest-mock requests locust bandit
cd src/sqa-automation
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

## Contribution Guidelines

Feel free to contribute to this repository by submitting issues or pull requests. Please follow the standard coding conventions and include appropriate documentation for any new features or changes.

## License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
