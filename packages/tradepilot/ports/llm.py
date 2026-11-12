from __future__ import annotations

from typing import Any, Mapping, Protocol


class LLMProvider(Protocol):
    """Explanation-only model boundary; implementations cannot access brokers."""

    @property
    def model_version(self) -> str: ...

    def explain(self, evidence: Mapping[str, Any]) -> Mapping[str, Any]: ...
