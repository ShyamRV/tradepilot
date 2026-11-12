from __future__ import annotations

from decimal import Decimal
from typing import Any


ALLOWED_FIELDS = {"close", "ema_fast", "ema_slow", "rsi", "macd", "signal"}
ALLOWED_OPS = {"gt", "gte", "lt", "lte", "crosses_above", "crosses_below"}

TEMPLATES: dict[str, dict[str, Any]] = {
    "ema_crossover": {"entry": {"op": "crosses_above", "left": "ema_fast", "right": "ema_slow"}, "exit": {"op": "crosses_below", "left": "ema_fast", "right": "ema_slow"}},
    "rsi_reversion": {"entry": {"op": "lt", "left": "rsi", "right": 30}, "exit": {"op": "gt", "left": "rsi", "right": 70}},
}


def validate_strategy(spec: dict[str, Any]) -> dict[str, Any]:
    if set(spec) != {"entry", "exit"}:
        raise ValueError("strategy requires only entry and exit")
    for rule in spec.values():
        if not isinstance(rule, dict) or set(rule) != {"op", "left", "right"}:
            raise ValueError("invalid rule shape")
        if rule["op"] not in ALLOWED_OPS or rule["left"] not in ALLOWED_FIELDS:
            raise ValueError("unsupported strategy expression")
        right = rule["right"]
        if not (right in ALLOWED_FIELDS if isinstance(right, str) else isinstance(right, (int, float))):
            raise ValueError("invalid right operand")
    return spec


def evaluate(rule: dict[str, Any], current: dict[str, Decimal], previous: dict[str, Decimal] | None = None) -> bool:
    left = current[rule["left"]]
    right_key = rule["right"]
    right = current[right_key] if isinstance(right_key, str) else Decimal(str(right_key))
    op = rule["op"]
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if previous is None or not isinstance(right_key, str):
        return False
    before_left, before_right = previous[rule["left"]], previous[right_key]
    return (before_left <= before_right and left > right) if op == "crosses_above" else (before_left >= before_right and left < right)
