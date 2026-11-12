from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Mapping


class GlmLLMProvider:
    """OpenAI-compatible chat client for GLM (Zhipu / OpenRouter / local).

    Explanation-only: never receives credentials or broker handles (ADR 0006).
    Falls back to a deterministic summary when unset or unreachable.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "glm-4")
        self.timeout_seconds = timeout_seconds

    @property
    def model_version(self) -> str:
        return f"glm:{self.model}" if self.base_url and self.api_key else "glm:fallback-v1"

    def explain(self, evidence: Mapping[str, Any]) -> Mapping[str, Any]:
        if not self.base_url or not self.api_key:
            return {
                "summary": _fallback_summary(evidence),
                "model_version": self.model_version,
                "provider": "fallback",
            }
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You explain paper-trading agent decisions. Use only the provided evidence. "
                        "Never promise returns. Never invent prices. Keep under 80 words."
                    ),
                },
                {"role": "user", "content": json.dumps(evidence, default=str)},
            ],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode())
            text = body["choices"][0]["message"]["content"].strip()
            return {"summary": text, "model_version": self.model_version, "provider": "glm"}
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, TimeoutError, json.JSONDecodeError):
            return {
                "summary": _fallback_summary(evidence),
                "model_version": self.model_version,
                "provider": "fallback",
            }


def _fallback_summary(evidence: Mapping[str, Any]) -> str:
    signal = evidence.get("signal") if isinstance(evidence.get("signal"), dict) else {}
    symbol = signal.get("symbol", "symbol")
    action = signal.get("action") or signal.get("side") or "hold"
    return f"Deterministic pipeline recommends {action} on {symbol}; model unavailable so this is a fallback explanation."
