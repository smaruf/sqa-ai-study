"""
Local LLM for SQA — 01: Ollama HTTP Client with Contract Tests
==============================================================
This module re-exports the shared OllamaClient from llm_client.py and
provides the contract test suite for it.

SQA concerns addressed:
- Contract testing: assert the API response schema never breaks
- Timeout enforcement: a slow model must not block the test suite indefinitely
- Error classification: distinguish network errors from model errors
- Mockability: every public method depends only on injected HTTP sessions

Ollama API reference: https://github.com/ollama/ollama/blob/main/docs/api.md

Run tests (no Ollama required — all mocked):
    pytest 01_llm_client.py -v

Run integration test against a live Ollama instance:
    OLLAMA_BASE_URL=http://localhost:11434 pytest 01_llm_client.py -v -m integration
"""

from unittest.mock import MagicMock

import pytest
import requests

# Re-export everything so other files can import from this module
from llm_client import (  # noqa: F401
    GenerateRequest,
    GenerateResponse,
    OllamaClient,
    OllamaConnectionError,
    OllamaError,
    OllamaRequestError,
    OllamaTimeoutError,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

MOCK_GENERATE_RESPONSE = {
    "model": "phi3:mini",
    "response": "Test case 1: Verify login with valid credentials.",
    "done": True,
    "total_duration": 4_500_000_000,  # 4.5 seconds in nanoseconds
}

MOCK_TAGS_RESPONSE = {
    "models": [
        {"name": "phi3:mini"},
        {"name": "qwen2.5:7b"},
    ]
}


@pytest.fixture
def mock_session():
    """HTTP session that returns canned Ollama responses."""
    session = MagicMock(spec=requests.Session)

    gen_resp = MagicMock()
    gen_resp.status_code = 200
    gen_resp.json.return_value = MOCK_GENERATE_RESPONSE
    gen_resp.raise_for_status = MagicMock()
    session.post.return_value = gen_resp

    tags_resp = MagicMock()
    tags_resp.status_code = 200
    tags_resp.json.return_value = MOCK_TAGS_RESPONSE
    tags_resp.raise_for_status = MagicMock()
    session.get.return_value = tags_resp

    return session


@pytest.fixture
def client(mock_session):
    return OllamaClient(base_url="http://localhost:11434", session=mock_session)


# ─── Contract Tests: GenerateResponse ─────────────────────────────────────────

class TestGenerateResponseContract:
    """Verify that GenerateResponse.from_dict() enforces the API contract."""

    def test_parses_valid_response(self):
        result = GenerateResponse.from_dict(MOCK_GENERATE_RESPONSE)
        assert result.model == "phi3:mini"
        assert result.response == "Test case 1: Verify login with valid credentials."
        assert result.done is True
        assert result.total_duration_ns == 4_500_000_000

    def test_raises_on_missing_response_field(self):
        bad = {k: v for k, v in MOCK_GENERATE_RESPONSE.items() if k != "response"}
        with pytest.raises(ValueError, match="response"):
            GenerateResponse.from_dict(bad)

    def test_raises_on_missing_done_field(self):
        bad = {k: v for k, v in MOCK_GENERATE_RESPONSE.items() if k != "done"}
        with pytest.raises(ValueError, match="done"):
            GenerateResponse.from_dict(bad)

    def test_raises_when_done_is_not_bool(self):
        bad = {**MOCK_GENERATE_RESPONSE, "done": "true"}
        with pytest.raises(ValueError, match="boolean"):
            GenerateResponse.from_dict(bad)

    def test_raises_when_response_is_not_string(self):
        bad = {**MOCK_GENERATE_RESPONSE, "response": 42}
        with pytest.raises(ValueError, match="string"):
            GenerateResponse.from_dict(bad)


# ─── Unit Tests: OllamaClient ─────────────────────────────────────────────────

class TestOllamaClientGenerate:

    def test_sends_correct_url(self, client, mock_session):
        req = GenerateRequest(model="phi3:mini", prompt="Hello")
        client.generate(req)
        call_url = mock_session.post.call_args[0][0]
        assert call_url == "http://localhost:11434/api/generate"

    def test_sends_stream_false_by_default(self, client, mock_session):
        req = GenerateRequest(model="phi3:mini", prompt="Hello")
        client.generate(req)
        payload = mock_session.post.call_args[1]["json"]
        assert payload["stream"] is False

    def test_returns_validated_response(self, client):
        req = GenerateRequest(model="phi3:mini", prompt="Hello")
        result = client.generate(req)
        assert isinstance(result, GenerateResponse)
        assert result.done is True

    def test_raises_connection_error_on_network_failure(self, mock_session):
        mock_session.post.side_effect = requests.exceptions.ConnectionError()
        client = OllamaClient(session=mock_session)
        with pytest.raises(OllamaConnectionError, match="ollama serve"):
            client.generate(GenerateRequest(model="phi3:mini", prompt="test"))

    def test_raises_timeout_error_on_slow_model(self, mock_session):
        mock_session.post.side_effect = requests.exceptions.Timeout()
        client = OllamaClient(session=mock_session)
        with pytest.raises(OllamaTimeoutError, match="quantized"):
            client.generate(GenerateRequest(model="phi3:mini", prompt="test"))

    def test_raises_request_error_on_http_400(self, mock_session):
        err_resp = MagicMock()
        err_resp.status_code = 400
        err_resp.text = '{"error":"model not found"}'
        mock_session.post.return_value = err_resp
        err_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=err_resp)
        client = OllamaClient(session=mock_session)
        with pytest.raises(OllamaRequestError):
            client.generate(GenerateRequest(model="no-such-model", prompt="test"))

    def test_enforces_timeout_parameter(self, client, mock_session):
        req = GenerateRequest(model="phi3:mini", prompt="Hello")
        client.generate(req)
        kwargs = mock_session.post.call_args[1]
        assert kwargs["timeout"] == OllamaClient.DEFAULT_TIMEOUT


class TestOllamaClientListModels:

    def test_returns_model_names(self, client):
        models = client.list_models()
        assert models == ["phi3:mini", "qwen2.5:7b"]

    def test_returns_empty_list_when_no_models_installed(self, mock_session):
        mock_session.get.return_value.json.return_value = {"models": []}
        client = OllamaClient(session=mock_session)
        assert client.list_models() == []

    def test_raises_connection_error_when_server_unreachable(self, mock_session):
        mock_session.get.side_effect = requests.exceptions.ConnectionError()
        client = OllamaClient(session=mock_session)
        with pytest.raises(OllamaConnectionError):
            client.list_models()


# ─── Integration Tests (require live Ollama) ──────────────────────────────────

@pytest.mark.integration
class TestOllamaIntegration:
    """
    Integration tests that run against a real Ollama instance.

    Prerequisites:
        ollama serve
        ollama pull phi3:mini

    Run with:
        OLLAMA_BASE_URL=http://localhost:11434 pytest 01_llm_client.py -v -m integration
    """

    def test_list_models_returns_at_least_one_model(self):
        client = OllamaClient()
        models = client.list_models()
        assert len(models) >= 1, (
            "No models found. Run `ollama pull phi3:mini` first."
        )

    def test_generate_returns_non_empty_response(self):
        client = OllamaClient()
        req = GenerateRequest(
            model="phi3:mini",
            prompt="Reply with exactly the word: PONG",
            options={"temperature": 0, "num_predict": 10},
        )
        result = client.generate(req)
        assert result.done is True
        assert len(result.response.strip()) > 0
        assert result.total_duration_ns > 0
