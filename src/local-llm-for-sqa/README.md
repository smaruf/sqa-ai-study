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
| `python/06_qwen3_thinking_mode.py` | Qwen3 thinking/non-thinking modes | Deep reasoning, audit evidence |

---

## Qwen3 — The Recommended Model for SQA Tasks

[**Qwen3**](https://github.com/QwenLM/Qwen3) (by Alibaba Cloud / QwenLM) is the top open-weight model for local SQA work on a laptop. Its standout feature for SQA is **thinking mode** — a built-in chain-of-thought that produces auditable reasoning before every answer.

### Why Qwen3 for SQA?

| Capability | SQA Application |
|-----------|----------------|
| **Thinking mode** (`<think>…</think>`) | Root cause analysis, coverage gap detection — the model shows its reasoning step-by-step |
| **Non-thinking mode** (`/no_think`) | Fast bug triage, quick test result classification — lower latency |
| **100+ languages** | Multilingual test artefacts, requirements in non-English |
| **Strong coding ability** | Generate test scripts, review test code, suggest refactors |
| **Tool use / function calling** | Agentic SQA pipelines, CI trigger decisions |
| **256K token context** (cloud/server) | Analyse large codebases, full test suite logs |

### Qwen3 Models for Laptop CPU (via Ollama)

| Ollama tag | Active params | RAM needed | Tokens/s* | Recommended for |
|-----------|--------------|-----------|-----------|----------------|
| `qwen3:4b` | 4 B | ~6 GB | 10–20 | Quick classification, fast drafts |
| `qwen3:8b` | 8 B | ~10 GB | 4–10 | Best balance — most SQA tasks |
| `qwen3:14b` | 14 B | ~18 GB | 2–5 | Deeper analysis (needs 32 GB RAM) |
| `qwen3:30b-a3b` | 3 B active / 30 B total | ~22 GB | 2–4 | MoE — high quality, high RAM cost |

\* CPU-only estimates on Intel Core Ultra. Always use Q4_K_M quantized builds (default in Ollama).

### Setup for Qwen3 on Your Laptop

```bash
# Install and start Ollama (https://ollama.com/download)
ollama serve

# Pull Qwen3 — start with 4b if RAM is tight, 8b for better SQA quality
ollama pull qwen3:4b
ollama pull qwen3:8b

# Set context window for long test artefacts (in Ollama CLI session)
/set parameter num_ctx 40960
/set parameter num_predict 32768

# Enable thinking mode (default for most Qwen3 models)
/set think

# Disable thinking for fast tasks
/set nothink
```

### Thinking vs Non-thinking Mode — When to Use Each

```
SQA Task                           Mode            Why
─────────────────────────────────────────────────────────────────────
Root cause analysis                Thinking ✅     Needs step-by-step reasoning
Coverage gap detection             Thinking ✅     Requires systematic analysis
Test strategy planning             Thinking ✅     Complex multi-factor decisions
Bug triage (severity)              Non-thinking    Speed matters; few labels
Test result classification         Non-thinking    Single label; deterministic
Quick test case title generation   Non-thinking    Low complexity, fast iteration
```

### Thinking Mode and SQA Auditability

The `<think>…</think>` block is not just a quirk — it is **audit evidence**.  
Store it alongside the final answer in your test reports or bug tracker:

```
Bug #1234 — AI Triage Decision
  Severity: High
  Reasoning (AI thinking trace):
    "The stack trace shows a null pointer in PaymentService.charge() on line 89.
     This is called from the main checkout flow — all users are affected.
     No workaround exists. This classifies as High."
  Final answer: High severity — assign to payment team, fix before release.
```

This makes AI-assisted SQA decisions **explainable and reviewable** by humans.

### OpenAI-Compatible API (Ollama v0.9.0+)

Ollama exposes an OpenAI-compatible endpoint at `http://localhost:11434/v1/`.  
You can use the `openai` Python SDK directly with Qwen3:

```python
import openai

client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Generate 3 test cases for a login form."}],
    max_tokens=2048,
)
print(response.choices[0].message.content)
```

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
