from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any


class OllamaError(RuntimeError):
    """Raised when the Ollama API cannot complete the request."""


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, model: str, messages: list[dict[str, Any]]) -> str:
        payload = {"model": model, "messages": messages, "stream": False}
        data = self._post_json("/api/chat", payload)
        try:
            return str(data["message"]["content"])
        except KeyError as exc:
            raise OllamaError(f"Unexpected Ollama response shape: {data}") from exc

    def vision_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        image_base64: str,
    ) -> str:
        if not messages:
            raise OllamaError("Vision chat requires at least one message.")
        vision_messages = [dict(message) for message in messages]
        vision_messages[-1]["images"] = [image_base64]
        return self.chat(model=model, messages=vision_messages)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(
                f"Ollama returned HTTP {exc.code} for {url}. Details: {details}"
            ) from exc
        except urllib.error.URLError as exc:
            raise OllamaError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Is `ollama serve` running, and is --ollama-url correct?"
            ) from exc
        except socket.timeout as exc:
            raise OllamaError(
                f"Ollama request timed out after {self.timeout:.0f} seconds."
            ) from exc

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise OllamaError(f"Ollama returned invalid JSON: {response_body}") from exc
        if "error" in parsed:
            raise OllamaError(f"Ollama error: {parsed['error']}")
        return parsed
