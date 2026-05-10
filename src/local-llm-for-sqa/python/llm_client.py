"""
Shared Ollama REST client used by all local-llm-for-sqa examples.

The numbered example files (01_*.py, 02_*.py, …) import from this module
so they can remain standalone runnable scripts while sharing a single
client implementation.

See 01_llm_client.py for the contract tests that cover this module.
"""

import os
from dataclasses import dataclass, field
from typing import Any

import requests


# ─── Data Contracts ───────────────────────────────────────────────────────────

@dataclass
class GenerateRequest:
    """Typed representation of a /api/generate payload."""
    model: str
    prompt: str
    stream: bool = False
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "prompt": self.prompt,
            "stream": self.stream,
            "options": self.options,
        }


@dataclass
class GenerateResponse:
    """Typed, validated wrapper around the Ollama /api/generate response."""
    model: str
    response: str
    done: bool
    total_duration_ns: int

    @classmethod
    def from_dict(cls, data: dict) -> "GenerateResponse":
        """Parse and validate raw response dict.

        Raises ValueError if required fields are missing — acting as a contract
        check that prevents callers from silently operating on partial data.
        """
        required = {"model", "response", "done", "total_duration"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Ollama response missing required fields: {missing}")
        if not isinstance(data["done"], bool):
            raise ValueError("Field 'done' must be a boolean")
        if not isinstance(data["response"], str):
            raise ValueError("Field 'response' must be a string")
        return cls(
            model=data["model"],
            response=data["response"],
            done=data["done"],
            total_duration_ns=data["total_duration"],
        )


# ─── Client ───────────────────────────────────────────────────────────────────

class OllamaClient:
    """Minimal Ollama REST client designed for testability.

    Accepts an optional `session` parameter so tests can inject a mock
    without patching global state.
    """

    DEFAULT_TIMEOUT = 120  # seconds — CPU inference is slow on laptops

    def __init__(
        self,
        base_url: str | None = None,
        session: requests.Session | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._session = session or requests.Session()
        self.timeout = timeout

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Send a non-streaming generate request and return a validated response."""
        url = f"{self.base_url}/api/generate"
        try:
            http_resp = self._session.post(
                url,
                json=request.to_dict(),
                timeout=self.timeout,
            )
            http_resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise OllamaConnectionError(
                f"Cannot reach Ollama at {self.base_url}. Is `ollama serve` running?"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {self.timeout} s. "
                "Try a smaller/more quantized model."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise OllamaRequestError(f"Ollama returned HTTP {http_resp.status_code}: {http_resp.text}") from exc

        return GenerateResponse.from_dict(http_resp.json())

    def list_models(self) -> list[str]:
        """Return the names of locally available models."""
        url = f"{self.base_url}/api/tags"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise OllamaConnectionError(f"Cannot reach Ollama at {self.base_url}") from exc
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]


# ─── Custom Exceptions ────────────────────────────────────────────────────────

class OllamaError(Exception):
    """Base class for Ollama client errors."""


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama server is unreachable."""


class OllamaTimeoutError(OllamaError):
    """Raised when inference exceeds the configured timeout."""


class OllamaRequestError(OllamaError):
    """Raised when the server returns a non-2xx HTTP status."""
