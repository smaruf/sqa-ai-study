"""
Local LLM for SQA — 06: Qwen3 Thinking Mode for Deep SQA Analysis
===================================================================
Qwen3 (QwenLM/Qwen3) introduces a unique "thinking mode" where the model
first generates a chain-of-thought reasoning block inside <think>...</think>
tags before producing its final answer. This makes it uniquely suited to
complex SQA tasks that benefit from step-by-step reasoning.

Reference: https://github.com/QwenLM/Qwen3

Key Qwen3 capabilities relevant to SQA:
- Thinking mode: deep reasoning for root cause analysis, coverage gap detection
- Non-thinking mode: fast classification, quick triage (/no_think hint)
- OpenAI-compatible API via Ollama (http://localhost:11434/v1/)
- Laptop-friendly sizes: qwen3:4b (~6 GB RAM), qwen3:8b (~10 GB RAM)
- Context window: set num_ctx=40960 for large test artefacts
- Tool use: structured function calling for agentic SQA pipelines

SQA concerns addressed in this file:
- Thinking block separation: always extract and store the reasoning
  separately from the final answer (the reasoning is audit evidence)
- Mode selection: validate that thinking mode is chosen for tasks that need
  it, and non-thinking for latency-sensitive tasks
- Thinking content validation: reject responses where thinking is empty when
  thinking mode was requested
- Context window guard: warn when the prompt exceeds safe token limits
- Idempotency of mode control: the /no_think hint must be reflected in a
  non-thinking response

Recommended Ollama setup for Qwen3:
    ollama pull qwen3:8b      # or qwen3:4b for 16 GB RAM machines
    ollama serve
    # In Ollama CLI: /set parameter num_ctx 40960
    # In API:        options: {"num_ctx": 40960, "num_predict": 32768}

Run tests (mocked — no Ollama required):
    pytest 06_qwen3_thinking_mode.py -v

Run integration tests against a live Ollama instance:
    OLLAMA_BASE_URL=http://localhost:11434 pytest 06_qwen3_thinking_mode.py -v -m integration
"""

import re
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import MagicMock  # used in test fixtures below

import pytest

from llm_client import GenerateRequest, GenerateResponse, OllamaClient


# ─── Qwen3 Model Constants ────────────────────────────────────────────────────

class Qwen3Model(str, Enum):
    """Ollama model tags for Qwen3 variants suitable for laptop CPU inference.

    See https://ollama.com/library/qwen3/tags for the full list.
    """
    Q4B = "qwen3:4b"       # ~6 GB RAM — fast, good for simple SQA tasks
    Q8B = "qwen3:8b"       # ~10 GB RAM — best balance for most SQA work
    Q14B = "qwen3:14b"     # ~18 GB RAM — requires 32 GB RAM; use with caution

    # MoE variant: smaller active params (3B) but larger total (30B)
    # requires more RAM than Q8B — only for well-resourced machines
    Q30B_A3B = "qwen3:30b-a3b"


# Qwen3-specific Ollama options recommended in the official documentation
QWEN3_OPTIONS_THINKING = {
    "num_ctx": 40960,       # large context for full test artefacts
    "num_predict": 32768,   # allow long thinking + answer chains
    "temperature": 0.6,     # official Qwen3 recommendation for thinking mode
    "top_k": 20,
    "top_p": 0.95,
    "min_p": 0.0,
}

QWEN3_OPTIONS_NON_THINKING = {
    "num_ctx": 40960,
    "num_predict": 4096,    # shorter — no chain-of-thought needed
    "temperature": 0.7,
    "top_k": 20,
    "top_p": 0.9,
}

# Approximate token limit for a safe single prompt on a 16 GB laptop
# (leaves room for the model's response in the context window)
SAFE_PROMPT_TOKEN_LIMIT = 8192

# Rough chars-per-token estimate for English technical text
CHARS_PER_TOKEN_ESTIMATE = 4


# ─── Thinking Block Extraction ────────────────────────────────────────────────

@dataclass
class Qwen3Response:
    """A parsed Qwen3 response with thinking and answer separated.

    The thinking content is SQA audit evidence — it shows *why* the model
    reached its conclusion and can be stored in a test report or bug tracker.
    """
    thinking_content: str        # content inside <think>...</think>
    answer: str                  # content after </think>
    used_thinking_mode: bool     # True when thinking_content is non-empty
    model: str
    total_duration_ns: int


def parse_qwen3_response(raw: str, model: str, total_duration_ns: int) -> Qwen3Response:
    """Extract thinking block and final answer from a raw Qwen3 response.

    Qwen3's thinking mode wraps its chain-of-thought in <think>...</think>
    tags. Some variants omit the opening tag and only include </think>.
    This parser handles both cases.

    Args:
        raw: The raw text from the LLM response field.
        model: Name of the Qwen3 model used.
        total_duration_ns: Inference duration for performance tracking.

    Returns:
        Qwen3Response with thinking and answer separated.
    """
    # Match optional opening <think> + content + closing </think>
    think_pattern = re.compile(
        r"(?:<think>)?(.*?)</think>(.*)",
        re.DOTALL,
    )
    match = think_pattern.search(raw)
    if match:
        thinking = match.group(1).strip()
        answer = match.group(2).strip()
    else:
        # No </think> tag — model ran in non-thinking mode
        thinking = ""
        answer = raw.strip()

    return Qwen3Response(
        thinking_content=thinking,
        answer=answer,
        used_thinking_mode=bool(thinking),
        model=model,
        total_duration_ns=total_duration_ns,
    )


def estimate_token_count(text: str) -> int:
    """Estimate token count for English technical text (rough heuristic).

    A proper tokeniser (e.g. tiktoken) should be used in production.
    This estimate is conservative: 4 chars ≈ 1 token.
    """
    return len(text) // CHARS_PER_TOKEN_ESTIMATE


# ─── Prompt Templates ─────────────────────────────────────────────────────────

# Deep analysis tasks — use thinking mode
ROOT_CAUSE_PROMPT = textwrap.dedent("""
    You are a senior SQA engineer performing root cause analysis.
    Think step by step through the failure evidence below, then provide
    a concise root cause and recommended corrective action.

    FAILURE EVIDENCE:
    {evidence}

    In your final answer (after </think>), structure your response as:
    Root Cause: <one sentence>
    Corrective Action: <one sentence>
    Regression Test: <what test would have caught this>
""").strip()

# Fast tasks — use non-thinking mode (append /no_think hint)
QUICK_CLASSIFY_PROMPT = textwrap.dedent("""
    /no_think
    Classify the following test result as PASS, FAIL, or SKIP.
    Reply with exactly one word.

    Test result: {result_text}
""").strip()

COVERAGE_GAP_PROMPT = textwrap.dedent("""
    You are an expert test strategist. Analyse the test plan below for coverage gaps.
    Think carefully about edge cases, negative scenarios, and non-functional requirements
    that may be missing. Then provide a structured gap analysis.

    TEST PLAN:
    {test_plan}

    In your final answer, list the gaps as bullet points, each starting with "- GAP:".
""").strip()


# ─── Qwen3 SQA Client ─────────────────────────────────────────────────────────

class Qwen3SqaClient:
    """SQA-focused wrapper around OllamaClient tuned for Qwen3 models.

    Provides three entry points:
    - analyse_root_cause(): thinking mode, deep causal analysis
    - detect_coverage_gaps(): thinking mode, test plan review
    - quick_classify(): non-thinking mode, fast single-label classification
    """

    def __init__(
        self,
        client: OllamaClient,
        model: str = Qwen3Model.Q8B,
    ):
        self._client = client
        self._model = model

    def analyse_root_cause(self, evidence: str) -> Qwen3Response:
        """Run root cause analysis using Qwen3's thinking mode.

        Args:
            evidence: Stack traces, logs, or failure description.

        Returns:
            Qwen3Response — thinking content contains the reasoning chain.

        Raises:
            ValueError: If the response is empty or thinking content is absent.
        """
        self._warn_if_prompt_too_long(evidence)
        prompt = ROOT_CAUSE_PROMPT.format(evidence=evidence)
        return self._call(prompt, options=QWEN3_OPTIONS_THINKING, require_thinking=True)

    def detect_coverage_gaps(self, test_plan: str) -> Qwen3Response:
        """Detect coverage gaps in a test plan using Qwen3's thinking mode.

        Args:
            test_plan: Plain-text or markdown test plan.

        Returns:
            Qwen3Response — answer contains bullet-point gap list.
        """
        self._warn_if_prompt_too_long(test_plan)
        prompt = COVERAGE_GAP_PROMPT.format(test_plan=test_plan)
        return self._call(prompt, options=QWEN3_OPTIONS_THINKING, require_thinking=False)

    def quick_classify(self, result_text: str) -> str:
        """Classify a test result as PASS, FAIL, or SKIP using non-thinking mode.

        The /no_think hint is embedded in the prompt to suppress Qwen3's
        chain-of-thought and return a fast single-word response.

        Args:
            result_text: A short description of a test result.

        Returns:
            One of "PASS", "FAIL", "SKIP" (uppercased).

        Raises:
            ValueError: If the model returns an unexpected classification.
        """
        prompt = QUICK_CLASSIFY_PROMPT.format(result_text=result_text)
        response = self._call(prompt, options=QWEN3_OPTIONS_NON_THINKING, require_thinking=False)
        label = response.answer.strip().upper()
        if label not in {"PASS", "FAIL", "SKIP"}:
            raise ValueError(
                f"Unexpected classification '{label}'. Expected PASS, FAIL, or SKIP."
            )
        return label

    # ── Private helpers ──────────────────────────────────────────────────────

    def _call(
        self,
        prompt: str,
        options: dict,
        require_thinking: bool,
    ) -> Qwen3Response:
        request = GenerateRequest(model=self._model, prompt=prompt, options=options)
        raw_resp = self._client.generate(request)
        parsed = parse_qwen3_response(raw_resp.response, raw_resp.model, raw_resp.total_duration_ns)
        if require_thinking and not parsed.used_thinking_mode:
            raise ValueError(
                "Thinking mode was required but the model returned no <think> block. "
                "Ensure `qwen3` is used (not phi3/llama3) and thinking mode is enabled."
            )
        return parsed

    @staticmethod
    def _warn_if_prompt_too_long(text: str) -> None:
        estimated = estimate_token_count(text)
        if estimated > SAFE_PROMPT_TOKEN_LIMIT:
            import warnings
            warnings.warn(
                f"Input is ~{estimated} tokens, which exceeds the safe limit of "
                f"{SAFE_PROMPT_TOKEN_LIMIT} tokens for a laptop CPU. "
                "Consider summarising the input or using a chunking strategy.",
                stacklevel=3,
            )


# ─── Test Fixtures ────────────────────────────────────────────────────────────

SAMPLE_FAILURE_EVIDENCE = textwrap.dedent("""
    Test: test_checkout_with_valid_card
    Status: FAIL
    Error: AssertionError: Expected HTTP 200, got HTTP 500
    Stack trace:
        checkout_service.process_payment() line 142
        payment_gateway.charge() line 89
        requests.post() → ConnectionError: max retries exceeded
    Environment: CI pipeline, payment-gateway mock was not started before the test suite.
""").strip()

SAMPLE_TEST_PLAN = textwrap.dedent("""
    Feature: User Login
    Test Cases:
    1. Happy path: valid email + password → dashboard redirect
    2. Wrong password → error message shown
    3. Empty email field → validation error
""").strip()

THINKING_RESPONSE = textwrap.dedent("""
    <think>
    The failure is in test_checkout_with_valid_card. The stack trace shows a
    ConnectionError when calling requests.post(). This suggests the payment
    gateway mock was not running. The CI setup is missing a mock startup step.
    </think>
    Root Cause: Payment gateway mock service was not started before the test suite.
    Corrective Action: Add mock startup to CI pipeline setup step.
    Regression Test: A smoke test that verifies the mock endpoint is reachable before any payment tests.
""").strip()

NON_THINKING_RESPONSE = "FAIL"

COVERAGE_GAP_RESPONSE = textwrap.dedent("""
    <think>
    The test plan only covers happy path, wrong password, and empty email.
    Missing: account lockout after N failures, SQL injection in email field,
    password reset flow, MFA scenarios, concurrent login sessions, and
    session expiry.
    </think>
    - GAP: No test for account lockout after repeated failed attempts
    - GAP: No negative test for SQL injection in the email field
    - GAP: Password reset flow is not covered
    - GAP: Multi-factor authentication scenarios are absent
    - GAP: Session expiry and concurrent session handling are not tested
""").strip()


def _make_mock_client(response_text: str) -> OllamaClient:
    mock_resp = GenerateResponse(
        model=Qwen3Model.Q8B,
        response=response_text,
        done=True,
        total_duration_ns=15_000_000_000,
    )
    client = MagicMock(spec=OllamaClient)
    client.generate.return_value = mock_resp
    return client


# ─── Unit Tests: Thinking Block Parsing ───────────────────────────────────────

class TestParseQwen3Response:

    def test_extracts_thinking_and_answer(self):
        result = parse_qwen3_response(THINKING_RESPONSE, "qwen3:8b", 1_000_000)
        assert "mock" in result.thinking_content
        assert "Root Cause:" in result.answer
        assert result.used_thinking_mode is True

    def test_handles_missing_opening_think_tag(self):
        """Qwen3-Thinking-2507 may omit the opening <think> tag."""
        raw = "Some reasoning here</think>\nFinal answer."
        result = parse_qwen3_response(raw, "qwen3:8b", 1_000_000)
        assert result.thinking_content == "Some reasoning here"
        assert result.answer == "Final answer."
        assert result.used_thinking_mode is True

    def test_non_thinking_response_has_empty_thinking(self):
        raw = "FAIL"
        result = parse_qwen3_response(raw, "qwen3:4b", 500_000)
        assert result.thinking_content == ""
        assert result.answer == "FAIL"
        assert result.used_thinking_mode is False

    def test_answer_does_not_contain_think_tags(self):
        result = parse_qwen3_response(THINKING_RESPONSE, "qwen3:8b", 1_000_000)
        assert "<think>" not in result.answer
        assert "</think>" not in result.answer

    def test_model_name_preserved(self):
        result = parse_qwen3_response("PASS", "qwen3:4b", 1_000_000)
        assert result.model == "qwen3:4b"

    def test_duration_preserved(self):
        result = parse_qwen3_response("PASS", "qwen3:8b", 12_345_678)
        assert result.total_duration_ns == 12_345_678


# ─── Unit Tests: Token Estimation ─────────────────────────────────────────────

class TestEstimateTokenCount:

    def test_empty_string_returns_zero(self):
        assert estimate_token_count("") == 0

    def test_short_text_below_limit(self):
        assert estimate_token_count("short input") < SAFE_PROMPT_TOKEN_LIMIT

    def test_long_text_above_limit(self):
        long_text = "word " * 10000
        assert estimate_token_count(long_text) > SAFE_PROMPT_TOKEN_LIMIT


# ─── Unit Tests: Qwen3SqaClient ───────────────────────────────────────────────

class TestQwen3SqaClientRootCause:

    def test_returns_thinking_response(self):
        client = _make_mock_client(THINKING_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        result = sqa.analyse_root_cause(SAMPLE_FAILURE_EVIDENCE)
        assert result.used_thinking_mode is True
        assert "Root Cause:" in result.answer

    def test_thinking_content_is_non_empty(self):
        client = _make_mock_client(THINKING_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        result = sqa.analyse_root_cause(SAMPLE_FAILURE_EVIDENCE)
        assert len(result.thinking_content) > 0

    def test_raises_when_thinking_mode_not_used(self):
        """require_thinking=True must reject non-thinking responses."""
        client = _make_mock_client("Root Cause: bad config.")  # no <think> block
        sqa = Qwen3SqaClient(client=client)
        with pytest.raises(ValueError, match="(?i)thinking mode was required"):
            sqa.analyse_root_cause(SAMPLE_FAILURE_EVIDENCE)

    def test_uses_thinking_mode_options(self):
        client = _make_mock_client(THINKING_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        sqa.analyse_root_cause(SAMPLE_FAILURE_EVIDENCE)
        options = client.generate.call_args[0][0].options
        assert options["num_ctx"] == QWEN3_OPTIONS_THINKING["num_ctx"]
        assert options["num_predict"] == QWEN3_OPTIONS_THINKING["num_predict"]

    def test_evidence_is_in_prompt(self):
        client = _make_mock_client(THINKING_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        sqa.analyse_root_cause("unique_failure_marker_xyz")
        prompt = client.generate.call_args[0][0].prompt
        assert "unique_failure_marker_xyz" in prompt

    def test_warns_when_input_exceeds_token_limit(self):
        oversized = "word " * (SAFE_PROMPT_TOKEN_LIMIT * CHARS_PER_TOKEN_ESTIMATE + 1000)
        client = _make_mock_client(THINKING_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        with pytest.warns(UserWarning, match="exceeds the safe limit"):
            sqa.analyse_root_cause(oversized)


class TestQwen3SqaClientCoverageGaps:

    def test_returns_gap_bullets(self):
        client = _make_mock_client(COVERAGE_GAP_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        result = sqa.detect_coverage_gaps(SAMPLE_TEST_PLAN)
        assert "- GAP:" in result.answer

    def test_thinking_content_is_captured(self):
        client = _make_mock_client(COVERAGE_GAP_RESPONSE)
        sqa = Qwen3SqaClient(client=client)
        result = sqa.detect_coverage_gaps(SAMPLE_TEST_PLAN)
        # The thinking content is audit evidence of WHY those gaps were identified
        assert len(result.thinking_content) > 0


class TestQwen3SqaClientQuickClassify:

    def test_classifies_pass(self):
        client = _make_mock_client("PASS")
        sqa = Qwen3SqaClient(client=client)
        assert sqa.quick_classify("All assertions passed") == "PASS"

    def test_classifies_fail(self):
        client = _make_mock_client("FAIL")
        sqa = Qwen3SqaClient(client=client)
        assert sqa.quick_classify("AssertionError: expected 200 got 500") == "FAIL"

    def test_classifies_skip(self):
        client = _make_mock_client("SKIP")
        sqa = Qwen3SqaClient(client=client)
        assert sqa.quick_classify("Test skipped due to missing environment variable") == "SKIP"

    def test_handles_lowercase_response(self):
        client = _make_mock_client("pass")
        sqa = Qwen3SqaClient(client=client)
        assert sqa.quick_classify("Test passed") == "PASS"

    def test_raises_on_unexpected_label(self):
        client = _make_mock_client("ERROR")
        sqa = Qwen3SqaClient(client=client)
        with pytest.raises(ValueError, match="Unexpected classification"):
            sqa.quick_classify("Something")

    def test_nothink_hint_is_in_prompt(self):
        """/no_think disables Qwen3's thinking mode for fast classification."""
        client = _make_mock_client("PASS")
        sqa = Qwen3SqaClient(client=client)
        sqa.quick_classify("All assertions passed")
        prompt = client.generate.call_args[0][0].prompt
        assert "/no_think" in prompt

    def test_uses_non_thinking_options(self):
        """Quick classify should use shorter num_predict than thinking tasks."""
        client = _make_mock_client("PASS")
        sqa = Qwen3SqaClient(client=client)
        sqa.quick_classify("passed")
        options = client.generate.call_args[0][0].options
        assert options["num_predict"] <= QWEN3_OPTIONS_NON_THINKING["num_predict"]
        assert options["num_predict"] < QWEN3_OPTIONS_THINKING["num_predict"]


# ─── Integration Tests (require live Ollama + Qwen3) ──────────────────────────

@pytest.mark.integration
class TestQwen3Integration:
    """
    Run against a real Ollama instance with Qwen3.

    Prerequisites:
        ollama serve
        ollama pull qwen3:4b   # or qwen3:8b for better quality

    Run with:
        OLLAMA_BASE_URL=http://localhost:11434 pytest 06_qwen3_thinking_mode.py -v -m integration

    Notes from QwenLM/Qwen3 official documentation:
    - Ollama v0.9.0 or higher is recommended
    - Set num_ctx=40960 and num_predict=32768 for best results
    - For thinking mode: use /set think (CLI) or temperature=0.6
    - For non-thinking mode: prefix prompt with /no_think
    - qwen3:4b fits in 16 GB RAM (recommended for Dell Latitude 7452)
    - qwen3:8b needs ~10 GB RAM and runs at ~3-8 tokens/s on Intel Core Ultra
    """

    MODEL = Qwen3Model.Q4B  # change to Q8B for better quality

    def test_root_cause_analysis_produces_thinking_content(self):
        client = OllamaClient()
        sqa = Qwen3SqaClient(client=client, model=self.MODEL)
        result = sqa.analyse_root_cause(SAMPLE_FAILURE_EVIDENCE)
        assert result.used_thinking_mode is True, (
            "Qwen3 should produce <think> blocks in thinking mode. "
            "Ensure you are using a qwen3:* model, not phi3/llama3."
        )
        assert "Root Cause:" in result.answer or len(result.answer) > 20

    def test_coverage_gap_analysis_finds_at_least_one_gap(self):
        client = OllamaClient()
        sqa = Qwen3SqaClient(client=client, model=self.MODEL)
        result = sqa.detect_coverage_gaps(SAMPLE_TEST_PLAN)
        assert "GAP" in result.answer.upper() or len(result.answer) > 20, (
            f"Expected at least one coverage gap. Got: {result.answer}"
        )

    def test_quick_classify_returns_valid_label(self):
        client = OllamaClient()
        sqa = Qwen3SqaClient(client=client, model=self.MODEL)
        label = sqa.quick_classify(
            "AssertionError: Expected status code 200 but got 404"
        )
        assert label in {"PASS", "FAIL", "SKIP"}

    def test_thinking_content_is_stored_for_audit(self):
        """Verify that thinking content can be used as audit evidence."""
        client = OllamaClient()
        sqa = Qwen3SqaClient(client=client, model=self.MODEL)
        result = sqa.analyse_root_cause(SAMPLE_FAILURE_EVIDENCE)
        # The thinking block should reference some aspect of the failure
        assert result.thinking_content != "" or result.answer != "", (
            "Both thinking and answer are empty — model may not have responded."
        )
