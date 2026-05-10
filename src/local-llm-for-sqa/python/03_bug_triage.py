"""
Local LLM for SQA — 03: Bug Triage with Consistency Quality Gates
=================================================================
Use a local LLM to classify bug report severity, then apply quality
gates to ensure consistency and reject low-confidence classifications.

SQA concerns addressed:
- Consistency gate: run the same report through the model twice and flag
  inconsistent classifications (non-determinism in a triage tool is a defect)
- Allowed-value enforcement: only accept defined severity levels
- Confidence signalling: if the model hedges its language, surface that as
  "requires human review"
- Audit trail: return a structured TriageResult that includes the raw
  reasoning, making the AI decision auditable and explainable

Run tests (mocked — no Ollama required):
    pytest 03_bug_triage.py -v

Run integration test against a live Ollama instance:
    OLLAMA_BASE_URL=http://localhost:11434 pytest 03_bug_triage.py -v -m integration
"""

import json
import re
import textwrap
from dataclasses import dataclass
from enum import Enum
from unittest.mock import MagicMock

import pytest

from python.01_llm_client import GenerateRequest, GenerateResponse, OllamaClient


# ─── Domain Types ─────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    REQUIRES_REVIEW = "RequiresReview"  # emitted when the model is uncertain


@dataclass
class BugReport:
    """A minimal bug report submitted for triage."""
    title: str
    description: str
    steps_to_reproduce: list[str]
    environment: str = ""

    def to_text(self) -> str:
        steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(self.steps_to_reproduce))
        return textwrap.dedent(f"""
            Title: {self.title}
            Description: {self.description}
            Steps to reproduce:
            {steps}
            Environment: {self.environment}
        """).strip()


@dataclass
class TriageResult:
    """Output of LLM-based triage — designed for auditability."""
    severity: Severity
    reasoning: str        # raw LLM reasoning, kept for human review
    needs_human_review: bool
    model_used: str
    raw_llm_output: str   # full response, useful for debugging hallucinations


# ─── Prompt Template ──────────────────────────────────────────────────────────

BUG_TRIAGE_PROMPT_V1 = textwrap.dedent("""
    You are a senior QA engineer performing bug triage. Classify the severity
    of the bug report below using ONLY one of: Critical, High, Medium, Low.

    Severity guidelines:
    - Critical: system is down, data loss, security breach, no workaround
    - High: major feature broken, significant user impact, workaround exists
    - Medium: feature partially broken, workaround available, moderate impact
    - Low: cosmetic issues, minor inconveniences, edge cases

    BUG REPORT:
    {bug_report}

    Respond in valid JSON only — no markdown, no prose outside the JSON:
    {{
      "severity": "<Critical|High|Medium|Low>",
      "reasoning": "<one or two sentences explaining your classification>"
    }}
""").strip()

# Phrases that indicate the model is uncertain — used to set needs_human_review
UNCERTAINTY_PATTERNS = [
    r"\bnot sure\b",
    r"\bunclear\b",
    r"\bcould be\b",
    r"\bmight be\b",
    r"\bhard to say\b",
    r"\bdifficult to determine\b",
    r"\bwithout more (information|context|details)\b",
]


# ─── Triage Engine ────────────────────────────────────────────────────────────

class BugTriageEngine:
    """Classifies bug severity using a local LLM.

    Quality gates:
    1. Allowed-value gate — only accepts the four defined severity levels
    2. Consistency gate — optionally runs the classification twice and flags
       disagreement (useful in CI pipelines or high-stakes triage)
    3. Uncertainty gate — detects hedging language in the reasoning and marks
       the result for human review
    """

    def __init__(self, client: OllamaClient, model: str = "phi3:mini"):
        self._client = client
        self._model = model

    def triage(self, bug: BugReport, consistency_check: bool = False) -> TriageResult:
        """Classify a bug report's severity.

        Args:
            bug: The bug report to classify.
            consistency_check: If True, runs a second classification and
                promotes the result to RequiresReview if the two passes disagree.

        Returns:
            TriageResult with severity, reasoning, and audit information.
        """
        result = self._run_once(bug)

        if consistency_check:
            second = self._run_once(bug)
            if second.severity != result.severity:
                return TriageResult(
                    severity=Severity.REQUIRES_REVIEW,
                    reasoning=(
                        f"Inconsistent classifications: pass 1={result.severity.value}, "
                        f"pass 2={second.severity.value}. Human review required."
                    ),
                    needs_human_review=True,
                    model_used=self._model,
                    raw_llm_output=f"Pass 1: {result.raw_llm_output}\nPass 2: {second.raw_llm_output}",
                )

        return result

    # ── Private helpers ──────────────────────────────────────────────────────

    def _run_once(self, bug: BugReport) -> TriageResult:
        prompt = BUG_TRIAGE_PROMPT_V1.format(bug_report=bug.to_text())
        request = GenerateRequest(
            model=self._model,
            prompt=prompt,
            options={"temperature": 0},  # deterministic — triage must be consistent
        )
        response = self._client.generate(request)
        return self._parse(response)

    def _parse(self, response: GenerateResponse) -> TriageResult:
        raw = response.response
        data = self._extract_json(raw)

        severity_str = str(data.get("severity", "")).strip()
        reasoning = str(data.get("reasoning", "")).strip()

        try:
            severity = Severity(severity_str)
        except ValueError:
            raise ValueError(
                f"LLM returned unrecognised severity '{severity_str}'. "
                f"Allowed values: {[s.value for s in Severity if s != Severity.REQUIRES_REVIEW]}"
            )

        needs_review = self._has_uncertainty(reasoning)

        return TriageResult(
            severity=severity,
            reasoning=reasoning,
            needs_human_review=needs_review,
            model_used=response.model,
            raw_llm_output=raw,
        )

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object found in LLM output: {text[:200]}")
        try:
            return json.loads(text[start: end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM output is not valid JSON: {text[:200]}") from exc

    @staticmethod
    def _has_uncertainty(reasoning: str) -> bool:
        lower = reasoning.lower()
        return any(re.search(p, lower) for p in UNCERTAINTY_PATTERNS)


# ─── Test Fixtures ────────────────────────────────────────────────────────────

CRASH_BUG = BugReport(
    title="App crashes on checkout when cart has more than 99 items",
    description="The payment flow throws an unhandled exception and the user loses their cart.",
    steps_to_reproduce=[
        "Add 100 items to the shopping cart",
        "Proceed to checkout",
        "Enter payment details and click 'Place Order'",
    ],
    environment="Production, iOS 17, App v4.2.1",
)

UI_BUG = BugReport(
    title="Button label 'Submitt' has a typo",
    description="The submit button on the contact form has a double-t typo.",
    steps_to_reproduce=["Navigate to /contact", "Observe the submit button label"],
    environment="All browsers",
)


def _make_mock_client(severity: str, reasoning: str = "Clear impact.") -> OllamaClient:
    response_json = json.dumps({"severity": severity, "reasoning": reasoning})
    mock_resp = GenerateResponse(
        model="phi3:mini",
        response=response_json,
        done=True,
        total_duration_ns=3_000_000_000,
    )
    client = MagicMock(spec=OllamaClient)
    client.generate.return_value = mock_resp
    return client


# ─── Unit Tests: JSON Extraction ──────────────────────────────────────────────

class TestExtractJson:

    def test_parses_clean_json_object(self):
        raw = '{"severity": "High", "reasoning": "Major feature broken."}'
        result = BugTriageEngine._extract_json(raw)
        assert result["severity"] == "High"

    def test_strips_markdown_fence(self):
        raw = '```json\n{"severity": "Low", "reasoning": "Typo."}\n```'
        result = BugTriageEngine._extract_json(raw)
        assert result["severity"] == "Low"

    def test_raises_when_no_json_object(self):
        with pytest.raises(ValueError, match="No JSON object"):
            BugTriageEngine._extract_json("I cannot classify this bug.")


# ─── Unit Tests: Uncertainty Detection ────────────────────────────────────────

class TestUncertaintyDetection:

    def test_detects_not_sure(self):
        assert BugTriageEngine._has_uncertainty("I'm not sure if this is High or Medium.")

    def test_detects_could_be(self):
        assert BugTriageEngine._has_uncertainty("This could be Critical depending on the data.")

    def test_detects_without_more_information(self):
        assert BugTriageEngine._has_uncertainty("Without more information I cannot be certain.")

    def test_confident_reasoning_is_not_flagged(self):
        assert not BugTriageEngine._has_uncertainty(
            "The app crashes in production causing data loss — this is clearly Critical."
        )


# ─── Unit Tests: BugTriageEngine ──────────────────────────────────────────────

class TestBugTriageEngine:

    def test_crash_bug_classified_as_high_or_critical(self):
        client = _make_mock_client("Critical", "Production crash causes data loss.")
        engine = BugTriageEngine(client=client)
        result = engine.triage(CRASH_BUG)
        assert result.severity in {Severity.CRITICAL, Severity.HIGH}
        assert result.needs_human_review is False

    def test_ui_bug_classified_as_low(self):
        client = _make_mock_client("Low", "Cosmetic typo with no functional impact.")
        engine = BugTriageEngine(client=client)
        result = engine.triage(UI_BUG)
        assert result.severity == Severity.LOW

    def test_result_includes_reasoning(self):
        client = _make_mock_client("Medium", "Moderate user impact.")
        engine = BugTriageEngine(client=client)
        result = engine.triage(CRASH_BUG)
        assert len(result.reasoning) > 0

    def test_result_includes_raw_llm_output_for_audit(self):
        client = _make_mock_client("High", "Major feature broken.")
        engine = BugTriageEngine(client=client)
        result = engine.triage(CRASH_BUG)
        assert len(result.raw_llm_output) > 0

    def test_raises_on_unrecognised_severity(self):
        client = _make_mock_client("Blocker", "Old Jira severity term.")
        engine = BugTriageEngine(client=client)
        with pytest.raises(ValueError, match="unrecognised severity"):
            engine.triage(CRASH_BUG)

    def test_uncertain_reasoning_sets_needs_human_review(self):
        client = _make_mock_client("Medium", "Could be High or Medium without more information.")
        engine = BugTriageEngine(client=client)
        result = engine.triage(CRASH_BUG)
        assert result.needs_human_review is True

    def test_temperature_zero_is_enforced(self):
        """Triage must use temperature=0 for consistency."""
        client = _make_mock_client("High")
        engine = BugTriageEngine(client=client)
        engine.triage(CRASH_BUG)
        options = client.generate.call_args[0][0].options
        assert options.get("temperature") == 0

    def test_consistency_check_passes_when_both_runs_agree(self):
        client = _make_mock_client("Critical", "Clear production impact.")
        engine = BugTriageEngine(client=client)
        result = engine.triage(CRASH_BUG, consistency_check=True)
        # Both calls return "Critical" — should not escalate
        assert result.severity == Severity.CRITICAL
        assert result.needs_human_review is False

    def test_consistency_check_escalates_when_runs_disagree(self):
        # Return "Critical" on first call, "Medium" on second
        resp1 = GenerateResponse(
            model="phi3:mini",
            response=json.dumps({"severity": "Critical", "reasoning": "Crash in prod."}),
            done=True,
            total_duration_ns=2_000_000_000,
        )
        resp2 = GenerateResponse(
            model="phi3:mini",
            response=json.dumps({"severity": "Medium", "reasoning": "Only edge case."}),
            done=True,
            total_duration_ns=2_000_000_000,
        )
        client = MagicMock(spec=OllamaClient)
        client.generate.side_effect = [resp1, resp2]

        engine = BugTriageEngine(client=client)
        result = engine.triage(CRASH_BUG, consistency_check=True)
        assert result.severity == Severity.REQUIRES_REVIEW
        assert result.needs_human_review is True
        assert "Inconsistent" in result.reasoning


# ─── Integration Tests (require live Ollama) ──────────────────────────────────

@pytest.mark.integration
class TestBugTriageIntegration:
    """
    Run against a real Ollama instance.

    Prerequisites:
        ollama serve
        ollama pull phi3:mini

    Run with:
        OLLAMA_BASE_URL=http://localhost:11434 pytest 03_bug_triage.py -v -m integration
    """

    def test_crash_bug_gets_high_or_critical_severity(self):
        client = OllamaClient()
        engine = BugTriageEngine(client=client, model="phi3:mini")
        result = engine.triage(CRASH_BUG)
        assert result.severity in {Severity.CRITICAL, Severity.HIGH, Severity.REQUIRES_REVIEW}, (
            f"Expected high-severity classification, got {result.severity}. "
            f"Reasoning: {result.reasoning}"
        )

    def test_typo_bug_does_not_get_critical_severity(self):
        client = OllamaClient()
        engine = BugTriageEngine(client=client, model="phi3:mini")
        result = engine.triage(UI_BUG)
        assert result.severity != Severity.CRITICAL, (
            f"A typo should not be Critical, got {result.severity}. "
            f"Reasoning: {result.reasoning}"
        )
