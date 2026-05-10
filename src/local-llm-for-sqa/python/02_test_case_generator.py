"""
Local LLM for SQA — 02: Test Case Generator with Output Validation
==================================================================
Ask a local LLM to generate test cases from a plain-English user story,
then apply SQA-grade validation before the output is trusted.

SQA concerns addressed:
- Output schema validation: enforce that generated test cases have the
  required fields (title, preconditions, steps, expected_result, priority)
- Quality gates: reject output that is too thin (too few test cases,
  empty steps, unrecognised priority values)
- Determinism in tests: mock the LLM so the unit test suite is reproducible
- Prompt versioning: prompts are named constants, not ad-hoc strings

Run tests (mocked — no Ollama required):
    pytest 02_test_case_generator.py -v

Run integration test against a live Ollama instance:
    OLLAMA_BASE_URL=http://localhost:11434 pytest 02_test_case_generator.py -v -m integration
"""

import json
import re
import textwrap
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from python.01_llm_client import (  # noqa: E402 — relative import within project
    GenerateRequest,
    GenerateResponse,
    OllamaClient,
)


# ─── Prompt Template (versioned) ──────────────────────────────────────────────

TEST_CASE_PROMPT_V1 = textwrap.dedent("""
    You are an expert software tester. Given the user story below, generate
    a list of test cases in **valid JSON** format only — no markdown, no prose.

    USER STORY:
    {user_story}

    OUTPUT FORMAT (JSON array, no other text):
    [
      {{
        "title": "<short test case title>",
        "preconditions": "<setup required before the test>",
        "steps": ["<step 1>", "<step 2>"],
        "expected_result": "<what should happen>",
        "priority": "<High|Medium|Low>"
      }}
    ]

    Generate at least {min_cases} test cases covering happy paths, edge cases,
    and negative/error scenarios.
""").strip()


# ─── Domain Types ─────────────────────────────────────────────────────────────

VALID_PRIORITIES = {"High", "Medium", "Low"}

REQUIRED_FIELDS = {"title", "preconditions", "steps", "expected_result", "priority"}


@dataclass
class TestCase:
    """A single validated test case produced by the LLM."""
    title: str
    preconditions: str
    steps: list[str]
    expected_result: str
    priority: str

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of {VALID_PRIORITIES}"
            )
        if not self.steps:
            raise ValueError("A test case must have at least one step")
        if not self.title.strip():
            raise ValueError("Test case title must not be blank")


# ─── Generator ────────────────────────────────────────────────────────────────

class TestCaseGenerator:
    """Uses a local LLM to generate test cases from a user story.

    Applies three layers of quality control:
    1. JSON parsing — rejects non-JSON responses immediately
    2. Schema validation — every field must be present with the right type
    3. Quality gate — enforces minimum test case count and content rules
    """

    def __init__(self, client: OllamaClient, model: str = "phi3:mini"):
        self._client = client
        self._model = model

    def generate(self, user_story: str, min_cases: int = 3) -> list[TestCase]:
        """Generate and validate test cases for the given user story.

        Args:
            user_story: A plain-English description of a feature or requirement.
            min_cases: Minimum number of test cases to accept. Output with fewer
                       cases is rejected as too thin.

        Returns:
            A list of validated TestCase objects.

        Raises:
            ValueError: If the LLM output fails parsing or quality checks.
        """
        prompt = TEST_CASE_PROMPT_V1.format(
            user_story=user_story.strip(),
            min_cases=min_cases,
        )
        request = GenerateRequest(
            model=self._model,
            prompt=prompt,
            options={"temperature": 0.2},  # lower temperature → more structured output
        )
        response = self._client.generate(request)
        return self._parse_and_validate(response.response, min_cases)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _parse_and_validate(self, raw: str, min_cases: int) -> list[TestCase]:
        """Extract JSON from the LLM output and validate each test case."""
        json_text = self._extract_json(raw)
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned non-JSON output. Raw response:\n{raw[:300]}"
            ) from exc

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array, got {type(data).__name__}")

        if len(data) < min_cases:
            raise ValueError(
                f"Quality gate: expected at least {min_cases} test cases, "
                f"got {len(data)}"
            )

        return [self._validate_case(i, item) for i, item in enumerate(data)]

    @staticmethod
    def _extract_json(text: str) -> str:
        """Strip markdown code fences and leading/trailing prose from LLM output."""
        # Remove ```json ... ``` or ``` ... ``` fences
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        # Find the first '[' to skip any leading prose
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found in LLM output")
        return text[start: end + 1]

    @staticmethod
    def _validate_case(index: int, item: Any) -> TestCase:
        """Validate a single test case dict and return a typed TestCase."""
        if not isinstance(item, dict):
            raise ValueError(f"Test case #{index} is not an object, got {type(item).__name__}")

        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"Test case #{index} is missing fields: {missing}")

        if not isinstance(item["steps"], list):
            raise ValueError(f"Test case #{index}: 'steps' must be an array")

        return TestCase(
            title=str(item["title"]),
            preconditions=str(item["preconditions"]),
            steps=[str(s) for s in item["steps"]],
            expected_result=str(item["expected_result"]),
            priority=str(item["priority"]),
        )


# ─── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_USER_STORY = """
As a registered user, I want to log in with my email and password
so that I can access my personal dashboard.
"""

VALID_LLM_OUTPUT = json.dumps([
    {
        "title": "Successful login with valid credentials",
        "preconditions": "User is registered with email user@example.com",
        "steps": [
            "Navigate to /login",
            "Enter email: user@example.com",
            "Enter password: correctPass123",
            "Click 'Log In'",
        ],
        "expected_result": "User is redirected to /dashboard",
        "priority": "High",
    },
    {
        "title": "Login fails with wrong password",
        "preconditions": "User is registered",
        "steps": [
            "Navigate to /login",
            "Enter email: user@example.com",
            "Enter wrong password",
            "Click 'Log In'",
        ],
        "expected_result": "Error message 'Invalid credentials' is displayed",
        "priority": "High",
    },
    {
        "title": "Login form validation — empty email",
        "preconditions": "None",
        "steps": [
            "Navigate to /login",
            "Leave email blank",
            "Enter any password",
            "Click 'Log In'",
        ],
        "expected_result": "Validation error 'Email is required' shown",
        "priority": "Medium",
    },
])


def _make_mock_client(llm_text: str) -> OllamaClient:
    """Return a mocked OllamaClient that returns a fixed text response."""
    mock_response = GenerateResponse(
        model="phi3:mini",
        response=llm_text,
        done=True,
        total_duration_ns=5_000_000_000,
    )
    client = MagicMock(spec=OllamaClient)
    client.generate.return_value = mock_response
    return client


# ─── Unit Tests: Output Parsing ───────────────────────────────────────────────

class TestExtractJson:

    def test_clean_json_array_passes_through(self):
        result = TestCaseGenerator._extract_json('[{"a":1}]')
        assert result == '[{"a":1}]'

    def test_strips_markdown_code_fence(self):
        raw = '```json\n[{"a":1}]\n```'
        result = TestCaseGenerator._extract_json(raw)
        assert json.loads(result) == [{"a": 1}]

    def test_strips_leading_prose(self):
        raw = 'Here are your test cases:\n[{"a":1}]'
        result = TestCaseGenerator._extract_json(raw)
        assert json.loads(result) == [{"a": 1}]

    def test_raises_when_no_json_array_found(self):
        with pytest.raises(ValueError, match="No JSON array"):
            TestCaseGenerator._extract_json("I cannot generate test cases.")


# ─── Unit Tests: TestCase Validation ──────────────────────────────────────────

class TestTestCaseValidation:

    def test_valid_test_case_parses_correctly(self):
        raw = {
            "title": "Happy path",
            "preconditions": "User logged in",
            "steps": ["Do X", "Click Y"],
            "expected_result": "Z happens",
            "priority": "High",
        }
        tc = TestCaseGenerator._validate_case(0, raw)
        assert tc.title == "Happy path"
        assert tc.priority == "High"
        assert len(tc.steps) == 2

    def test_raises_on_missing_field(self):
        raw = {"title": "T", "steps": ["S"], "expected_result": "E", "priority": "Low"}
        with pytest.raises(ValueError, match="preconditions"):
            TestCaseGenerator._validate_case(0, raw)

    def test_raises_on_invalid_priority(self):
        raw = {
            "title": "T", "preconditions": "P",
            "steps": ["S"], "expected_result": "E", "priority": "Critical",
        }
        with pytest.raises(ValueError, match="Invalid priority"):
            TestCaseGenerator._validate_case(0, raw)

    def test_raises_on_empty_steps(self):
        raw = {
            "title": "T", "preconditions": "P",
            "steps": [], "expected_result": "E", "priority": "Low",
        }
        with pytest.raises(ValueError, match="at least one step"):
            TestCaseGenerator._validate_case(0, raw)

    def test_raises_on_blank_title(self):
        raw = {
            "title": "   ", "preconditions": "P",
            "steps": ["S"], "expected_result": "E", "priority": "Low",
        }
        with pytest.raises(ValueError, match="title must not be blank"):
            TestCaseGenerator._validate_case(0, raw)

    def test_steps_must_be_array(self):
        raw = {
            "title": "T", "preconditions": "P",
            "steps": "Step 1, Step 2", "expected_result": "E", "priority": "Low",
        }
        with pytest.raises(ValueError, match="'steps' must be an array"):
            TestCaseGenerator._validate_case(0, raw)


# ─── Unit Tests: Generator ────────────────────────────────────────────────────

class TestTestCaseGenerator:

    def test_returns_list_of_validated_test_cases(self):
        client = _make_mock_client(VALID_LLM_OUTPUT)
        gen = TestCaseGenerator(client=client)
        cases = gen.generate(SAMPLE_USER_STORY, min_cases=3)
        assert len(cases) == 3
        assert all(isinstance(tc, TestCase) for tc in cases)

    def test_includes_prompt_with_user_story(self):
        client = _make_mock_client(VALID_LLM_OUTPUT)
        gen = TestCaseGenerator(client=client)
        gen.generate("As a user I want X", min_cases=3)
        prompt_used = client.generate.call_args[0][0].prompt
        assert "As a user I want X" in prompt_used

    def test_quality_gate_rejects_too_few_cases(self):
        one_case = json.dumps([json.loads(VALID_LLM_OUTPUT)[0]])
        client = _make_mock_client(one_case)
        gen = TestCaseGenerator(client=client)
        with pytest.raises(ValueError, match="Quality gate"):
            gen.generate(SAMPLE_USER_STORY, min_cases=3)

    def test_raises_on_non_json_response(self):
        client = _make_mock_client("Sorry, I cannot help with that.")
        gen = TestCaseGenerator(client=client)
        with pytest.raises(ValueError, match="non-JSON"):
            gen.generate(SAMPLE_USER_STORY, min_cases=1)

    def test_raises_when_llm_returns_object_not_array(self):
        client = _make_mock_client('{"error": "oops"}')
        gen = TestCaseGenerator(client=client)
        with pytest.raises(ValueError, match="JSON array"):
            gen.generate(SAMPLE_USER_STORY, min_cases=1)

    def test_low_temperature_option_is_set(self):
        client = _make_mock_client(VALID_LLM_OUTPUT)
        gen = TestCaseGenerator(client=client)
        gen.generate(SAMPLE_USER_STORY, min_cases=3)
        options = client.generate.call_args[0][0].options
        assert options.get("temperature", 1.0) <= 0.3, (
            "Use low temperature for structured JSON output"
        )


# ─── Integration Tests (require live Ollama) ──────────────────────────────────

@pytest.mark.integration
class TestTestCaseGeneratorIntegration:
    """
    Run against a real Ollama instance.

    Prerequisites:
        ollama serve
        ollama pull phi3:mini

    Run with:
        OLLAMA_BASE_URL=http://localhost:11434 pytest 02_test_case_generator.py -v -m integration
    """

    def test_generates_valid_test_cases_from_login_story(self):
        client = OllamaClient()
        gen = TestCaseGenerator(client=client, model="phi3:mini")
        cases = gen.generate(SAMPLE_USER_STORY, min_cases=2)
        assert len(cases) >= 2
        for tc in cases:
            assert tc.priority in VALID_PRIORITIES
            assert len(tc.steps) >= 1
