# Local LLM for SQA — Practical Guide & Examples

Run AI models **locally** on your laptop and apply them to Software Quality Assurance tasks.  
No cloud account required. Zero cost. Full data privacy.

---

## Why Local LLM for SQA?

| Concern | Cloud LLM | Local LLM |
|---------|-----------|-----------|
| **Privacy** | Test artefacts leave your network | Stays on your machine |
| **Cost** | Per-token billing | Free after setup |
| **Availability** | Requires internet | Works offline |
| **Latency** | ~0.5–3 s round-trip | ~1–8 s on laptop CPU |
| **Compliance** | Data residency issues | No third-party data sharing |

SQA artefacts — test cases, bug reports, user stories, credentials in test configs — are often **sensitive**. A local LLM lets you use AI assistance without leaking those artefacts to external services.

---

## Hardware Requirements (based on Dell Latitude 7452)

| Component | Specification | Notes |
|-----------|--------------|-------|
| **CPU** | Intel Core Ultra 5/7 (12–14 cores) | Primary compute for inference |
| **RAM** | 16 GB LPDDR5x | Minimum for 7 B models |
| **GPU** | Intel Integrated / Arc (shared memory) | No dedicated VRAM |
| **Storage** | 20 GB free | Model files are 4–8 GB each |
| **OS** | Windows 11 / Linux | Both supported by Ollama |

### Recommended Models for SQA Tasks

| Model | Size | RAM | Tokens/s* | Best SQA Use |
|-------|------|-----|-----------|--------------|
| `phi3:mini` | 3.8 B | ~6 GB | 15–30 | Quick drafts, simple triage |
| `qwen2.5:7b` | 7 B | ~8 GB | 5–12 | Balanced reasoning, test gen |
| `llama3.1:8b` | 8 B | ~10 GB | 3–8 | High-quality test plans |
| `gemma2:9b` | 9 B | ~12 GB | 2–6 | Analysis, creative test ideas |

\* Tokens/s are CPU-inference estimates on Intel Core Ultra. Always use **Q4_K_M quantized** versions.

> ⚠️ Models **13 B+** will crash or run unusably slowly on integrated-graphics laptops.  
> ✅ Always pick the Q4 or Q5 quantized variant (label: `Q4_K_M`, `Q5_K_M`).

---

## Quickstart with Ollama

```bash
# 1. Install Ollama (https://ollama.com/download)
# 2. Pull a model
ollama pull phi3:mini          # lightest, fastest
ollama pull qwen2.5:7b         # recommended for SQA work

# 3. Start the server (runs at http://localhost:11434)
ollama serve

# 4. Test the connection
curl http://localhost:11434/api/tags
```

---

## SQA Tasks Covered in This Project

| File | Topic | SQA Concern |
|------|-------|-------------|
| `python/01_llm_client.py` | Ollama REST client + contract tests | API reliability, response schema |
| `python/02_test_case_generator.py` | Test case generation from user stories | Output validation, coverage gaps |
| `python/03_bug_triage.py` | Bug severity classification | Consistency, quality gates |
| `python/04_test_data_factory.py` | Structured test data generation | Schema validation, edge cases |
| `python/05_prompt_safety.py` | Prompt injection prevention | Security, input sanitisation |

---

## Core SQA Principles Applied to Local LLMs

### 1. Mock the LLM in Unit Tests
LLM responses are non-deterministic. Unit tests must not depend on a live model.  
Use `unittest.mock` or `pytest-mock` to stub `requests.post` with canned responses.

### 2. Schema-Validate Every LLM Output
An LLM can hallucinate structure. Always parse and validate the output before use:
```python
import json, jsonschema
data = json.loads(llm_response)
jsonschema.validate(data, EXPECTED_SCHEMA)
```

### 3. Quality Gates — Reject Bad Outputs
Define minimum acceptance criteria and retry or escalate when they fail:
- Required fields present
- Enum values within allowed set
- Minimum list length for test case output

### 4. Prompt Versioning
Treat prompts as production artefacts, not ad-hoc strings:
- Store them as named constants or in a `prompts/` directory
- Version them alongside code
- Pin the model name + version in CI

### 5. Latency Budget
LLMs on laptop CPUs are slow. Set an explicit timeout:
```python
response = requests.post(url, json=payload, timeout=120)
```
Document the expected tokens/s for each model so testers set expectations correctly.

### 6. Prompt Injection Prevention
Never interpolate untrusted user input directly into a prompt without sanitisation.  
Treat the prompt + input separation the same way you treat SQL + parameters.

---

## Running the Tests

```bash
# Install dependencies
pip install pytest pytest-mock requests jsonschema

# Run all tests (mocked — no Ollama needed)
cd src/local-llm-for-sqa/python
pytest -v

# Run integration tests against a live Ollama instance
OLLAMA_BASE_URL=http://localhost:11434 pytest -v -m integration
```

---

## Performance Expectations on Laptop CPU

| Task | Model | Expected Time | Notes |
|------|-------|--------------|-------|
| Single test case generation | phi3:mini | 5–15 s | Good for quick drafts |
| Bug severity triage | qwen2.5:7b | 10–30 s | Better accuracy |
| Test suite from user story | llama3.1:8b | 30–90 s | Best quality |
| Test data JSON (10 rows) | phi3:mini | 15–40 s | Validate output schema |

🔋 **Tip**: Plug in your laptop. CPU inference discharges the battery significantly.

---

## Further Reading

- [Ollama documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Model quantization explained](https://huggingface.co/docs/optimum/concept_guides/quantization)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [SQA Automation Learning Path](../sqa-automation/README.md)
