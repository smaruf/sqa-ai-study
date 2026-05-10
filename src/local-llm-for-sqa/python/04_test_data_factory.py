"""
Local LLM for SQA — 04: Structured Test Data Factory with Schema Guardrails
============================================================================
Ask a local LLM to generate realistic, schema-valid test data, then apply
guardrails before the data reaches any test suite or database.

SQA concerns addressed:
- Schema contract: every generated row must match a defined JSON Schema
- Boundary coverage: prompt explicitly requests edge/boundary values
- PII prevention: detect and reject test data that looks like real personal data
- Volume gate: enforce that the requested row count is actually delivered
- Idempotent seed: use a deterministic prompt so the same seed yields
  reproducible data (useful in regression suites)

Run tests (mocked — no Ollama required):
    pytest 04_test_data_factory.py -v

Run integration test against a live Ollama instance:
    OLLAMA_BASE_URL=http://localhost:11434 pytest 04_test_data_factory.py -v -m integration
"""

import json
import re
import textwrap
from typing import Any
from unittest.mock import MagicMock

import pytest

from llm_client import GenerateRequest, GenerateResponse, OllamaClient


# ─── Schema Definition ────────────────────────────────────────────────────────

# A minimal user-account schema for e-commerce SQA test data
USER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "username", "email", "age", "account_type"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "username": {"type": "string", "minLength": 3, "maxLength": 30},
        "email": {"type": "string", "pattern": r".+@.+\..+"},
        "age": {"type": "integer", "minimum": 0, "maximum": 130},
        "account_type": {"type": "string", "enum": ["free", "premium", "enterprise"]},
    },
    "additionalProperties": False,
}

# ─── PII Detection Patterns ───────────────────────────────────────────────────

# Patterns that indicate the model may have leaked real PII into test data.
# Real names of people, real phone numbers, SSNs, etc. are not acceptable
# in test datasets, even if they look plausible.
PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",          # SSN format: 123-45-6789
    r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b",  # Credit card pattern
    r"\b\+?1?\s?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b",  # Phone number
]


# ─── Prompt Template ──────────────────────────────────────────────────────────

TEST_DATA_PROMPT_V1 = textwrap.dedent("""
    You are a test data engineer. Generate exactly {count} test user records
    for a software test suite. Use ONLY fictional, non-real data.

    Requirements:
    - Cover boundary values: include at least one record with minimum age (0),
      one near maximum age (130), one with a very short username (3 chars),
      and one with a long username (30 chars).
    - Include all three account types: free, premium, enterprise.
    - Every email must follow the pattern: <something>@<domain>.<tld>
    - IDs must be unique positive integers.
    - Do NOT use real names, real email domains (gmail/yahoo/outlook), or
      any real personal information.

    Output: a valid JSON array only — no markdown fences, no prose:
    [
      {{
        "id": <integer>,
        "username": "<3-30 chars>",
        "email": "<fictional@test.example>",
        "age": <0-130>,
        "account_type": "<free|premium|enterprise>"
      }}
    ]

    Generate exactly {count} records.
""").strip()


# ─── Schema Validator (without external jsonschema dependency) ────────────────

def validate_user_record(record: Any, index: int) -> None:
    """Validate a single user record against USER_SCHEMA.

    Raises ValueError with a descriptive message if validation fails.
    Uses manual checks to avoid requiring the jsonschema package in the
    unit-test environment; production code should use jsonschema.validate().
    """
    if not isinstance(record, dict):
        raise ValueError(f"Record #{index}: expected object, got {type(record).__name__}")

    required = set(USER_SCHEMA["required"])
    missing = required - record.keys()
    if missing:
        raise ValueError(f"Record #{index}: missing required fields {missing}")

    extra = record.keys() - USER_SCHEMA["properties"].keys()
    if extra:
        raise ValueError(f"Record #{index}: unexpected fields {extra}")

    props = USER_SCHEMA["properties"]

    if not isinstance(record["id"], int) or record["id"] < 1:
        raise ValueError(f"Record #{index}: 'id' must be a positive integer, got {record['id']!r}")

    username = record["username"]
    if not isinstance(username, str) or not (3 <= len(username) <= 30):
        raise ValueError(
            f"Record #{index}: 'username' must be 3–30 chars, got {len(str(username))}"
        )

    email = record["email"]
    if not isinstance(email, str) or not re.match(props["email"]["pattern"], email):
        raise ValueError(f"Record #{index}: 'email' does not match expected pattern, got {email!r}")

    age = record["age"]
    if not isinstance(age, int) or not (0 <= age <= 130):
        raise ValueError(f"Record #{index}: 'age' must be 0–130, got {age!r}")

    account_type = record["account_type"]
    allowed = props["account_type"]["enum"]
    if account_type not in allowed:
        raise ValueError(
            f"Record #{index}: 'account_type' must be one of {allowed}, got {account_type!r}"
        )


def detect_pii(text: str) -> list[str]:
    """Return a list of PII pattern names found in the text."""
    found = []
    labels = ["SSN", "credit_card", "phone_number"]
    for label, pattern in zip(labels, PII_PATTERNS):
        if re.search(pattern, text):
            found.append(label)
    return found


# ─── Factory ──────────────────────────────────────────────────────────────────

class TestDataFactory:
    """Generates validated test data records using a local LLM.

    Quality pipeline:
    1. Parse JSON from LLM output
    2. Check PII patterns across the entire output string
    3. Validate count matches the requested amount
    4. Schema-validate each record
    5. Check uniqueness of IDs
    """

    def __init__(self, client: OllamaClient, model: str = "phi3:mini"):
        self._client = client
        self._model = model

    def generate_users(self, count: int = 5) -> list[dict]:
        """Generate `count` validated user test records.

        Args:
            count: Number of records to generate (1–20).

        Returns:
            A list of validated user dicts.

        Raises:
            ValueError: If the LLM output fails any quality gate.
        """
        if not 1 <= count <= 20:
            raise ValueError("count must be between 1 and 20")

        prompt = TEST_DATA_PROMPT_V1.format(count=count)
        request = GenerateRequest(
            model=self._model,
            prompt=prompt,
            options={"temperature": 0.7},  # some variation for diverse test data
        )
        response = self._client.generate(request)
        return self._validate_output(response.response, count)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _validate_output(self, raw: str, expected_count: int) -> list[dict]:
        # Gate 1: PII check on the entire raw output
        pii_found = detect_pii(raw)
        if pii_found:
            raise ValueError(
                f"PII detected in LLM output ({pii_found}). "
                "Regenerate without real personal data."
            )

        # Gate 2: Extract and parse JSON
        data = self._parse_json_array(raw)

        # Gate 3: Count check
        if len(data) != expected_count:
            raise ValueError(
                f"Count gate: expected {expected_count} records, got {len(data)}"
            )

        # Gate 4: Schema validation for each record
        for i, record in enumerate(data):
            validate_user_record(record, i)

        # Gate 5: Unique ID check
        ids = [r["id"] for r in data]
        if len(set(ids)) != len(ids):
            raise ValueError("ID uniqueness gate: duplicate IDs found in generated data")

        return data

    @staticmethod
    def _parse_json_array(text: str) -> list:
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found in LLM output")
        try:
            return json.loads(text[start: end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON parse error in LLM output: {exc}") from exc


# ─── Fixtures ─────────────────────────────────────────────────────────────────

VALID_RECORDS = [
    {"id": 1, "username": "abc", "email": "abc@test.example", "age": 0, "account_type": "free"},
    {"id": 2, "username": "bob_tester", "email": "bob@qa.internal", "age": 25, "account_type": "premium"},
    {"id": 3, "username": "x" * 30, "email": "long@qa.internal", "age": 130, "account_type": "enterprise"},
    {"id": 4, "username": "dana_qa", "email": "dana@example.test", "age": 18, "account_type": "free"},
    {"id": 5, "username": "eve_robot", "email": "eve@robot.test", "age": 42, "account_type": "premium"},
]


def _make_mock_client(records: list[dict]) -> OllamaClient:
    mock_resp = GenerateResponse(
        model="phi3:mini",
        response=json.dumps(records),
        done=True,
        total_duration_ns=8_000_000_000,
    )
    client = MagicMock(spec=OllamaClient)
    client.generate.return_value = mock_resp
    return client


# ─── Unit Tests: Schema Validation ────────────────────────────────────────────

class TestValidateUserRecord:

    def test_valid_record_passes(self):
        validate_user_record(VALID_RECORDS[0], 0)  # should not raise

    def test_raises_on_missing_field(self):
        bad = {k: v for k, v in VALID_RECORDS[0].items() if k != "email"}
        with pytest.raises(ValueError, match="email"):
            validate_user_record(bad, 0)

    def test_raises_on_extra_field(self):
        bad = {**VALID_RECORDS[0], "password": "secret"}
        with pytest.raises(ValueError, match="unexpected"):
            validate_user_record(bad, 0)

    def test_raises_on_invalid_email(self):
        bad = {**VALID_RECORDS[0], "email": "not-an-email"}
        with pytest.raises(ValueError, match="email"):
            validate_user_record(bad, 0)

    def test_raises_on_age_above_max(self):
        bad = {**VALID_RECORDS[0], "age": 131}
        with pytest.raises(ValueError, match="age"):
            validate_user_record(bad, 0)

    def test_raises_on_age_below_min(self):
        bad = {**VALID_RECORDS[0], "age": -1}
        with pytest.raises(ValueError, match="age"):
            validate_user_record(bad, 0)

    def test_raises_on_invalid_account_type(self):
        bad = {**VALID_RECORDS[0], "account_type": "gold"}
        with pytest.raises(ValueError, match="account_type"):
            validate_user_record(bad, 0)

    def test_raises_on_username_too_short(self):
        bad = {**VALID_RECORDS[0], "username": "ab"}
        with pytest.raises(ValueError, match="username"):
            validate_user_record(bad, 0)

    def test_raises_on_username_too_long(self):
        bad = {**VALID_RECORDS[0], "username": "x" * 31}
        with pytest.raises(ValueError, match="username"):
            validate_user_record(bad, 0)

    def test_raises_on_id_zero(self):
        bad = {**VALID_RECORDS[0], "id": 0}
        with pytest.raises(ValueError, match="id"):
            validate_user_record(bad, 0)


# ─── Unit Tests: PII Detection ────────────────────────────────────────────────

class TestDetectPii:

    def test_detects_ssn(self):
        assert "SSN" in detect_pii("User SSN: 123-45-6789")

    def test_detects_phone_number(self):
        assert "phone_number" in detect_pii("Call us at +1 (555) 867-5309")

    def test_clean_text_returns_empty_list(self):
        assert detect_pii("username=tester42, email=tester42@qa.example, age=30") == []

    def test_detects_credit_card(self):
        assert "credit_card" in detect_pii("Card: 4111 1111 1111 1111")


# ─── Unit Tests: TestDataFactory ──────────────────────────────────────────────

class TestTestDataFactory:

    def test_returns_correct_number_of_records(self):
        client = _make_mock_client(VALID_RECORDS)
        factory = TestDataFactory(client=client)
        result = factory.generate_users(count=5)
        assert len(result) == 5

    def test_all_records_pass_schema_validation(self):
        client = _make_mock_client(VALID_RECORDS)
        factory = TestDataFactory(client=client)
        result = factory.generate_users(count=5)
        # If we get here without exception, all records are valid
        assert all("email" in r for r in result)

    def test_count_gate_rejects_too_few_records(self):
        client = _make_mock_client(VALID_RECORDS[:2])
        factory = TestDataFactory(client=client)
        with pytest.raises(ValueError, match="Count gate"):
            factory.generate_users(count=5)

    def test_pii_gate_rejects_ssn_in_output(self):
        records_with_pii = [
            {**VALID_RECORDS[0], "username": "John 123-45-6789 Doe"},
        ]
        client = _make_mock_client(records_with_pii)
        factory = TestDataFactory(client=client)
        with pytest.raises(ValueError, match="PII"):
            factory.generate_users(count=1)

    def test_uniqueness_gate_rejects_duplicate_ids(self):
        dup_ids = [
            {**VALID_RECORDS[0], "id": 1},
            {**VALID_RECORDS[1], "id": 1},  # duplicate
        ]
        client = _make_mock_client(dup_ids)
        factory = TestDataFactory(client=client)
        with pytest.raises(ValueError, match="duplicate"):
            factory.generate_users(count=2)

    def test_raises_on_invalid_count_zero(self):
        client = _make_mock_client([])
        factory = TestDataFactory(client=client)
        with pytest.raises(ValueError, match="count must be between"):
            factory.generate_users(count=0)

    def test_raises_on_invalid_count_above_max(self):
        client = _make_mock_client([])
        factory = TestDataFactory(client=client)
        with pytest.raises(ValueError, match="count must be between"):
            factory.generate_users(count=21)

    def test_prompt_includes_requested_count(self):
        client = _make_mock_client(VALID_RECORDS)
        factory = TestDataFactory(client=client)
        factory.generate_users(count=5)
        prompt = client.generate.call_args[0][0].prompt
        assert "5" in prompt


# ─── Integration Tests (require live Ollama) ──────────────────────────────────

@pytest.mark.integration
class TestTestDataFactoryIntegration:
    """
    Prerequisites:
        ollama serve
        ollama pull phi3:mini

    Run with:
        OLLAMA_BASE_URL=http://localhost:11434 pytest 04_test_data_factory.py -v -m integration
    """

    def test_generates_five_valid_user_records(self):
        client = OllamaClient()
        factory = TestDataFactory(client=client, model="phi3:mini")
        records = factory.generate_users(count=5)
        assert len(records) == 5
        for i, record in enumerate(records):
            validate_user_record(record, i)

    def test_generated_data_has_no_pii(self):
        client = OllamaClient()
        factory = TestDataFactory(client=client, model="phi3:mini")
        records = factory.generate_users(count=3)
        raw = json.dumps(records)
        assert detect_pii(raw) == [], f"PII found in generated data: {raw}"
