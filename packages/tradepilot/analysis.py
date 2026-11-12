from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from .indicators import atr, ema, macd, rsi
from .market import Dataset
from .strategy import evaluate, validate_strategy


@dataclass(frozen=True)
class Analysis:
    id: str
    dataset_id: str
    symbol: str
    session: str
    indicators: dict[str, Decimal | None]
    evidence: dict[str, dict[str, Any]]
    dataset_checksum: str
    strategy_hash: str
    engine_version: str
    created_at: datetime


def analyze(dataset: Dataset, strategy: dict[str, Any], analysis_id: str) -> Analysis:
    if dataset.status != "published":
        raise ValueError("analysis requires a published dataset")
    validate_strategy(strategy)
    closes = [bar.close for bar in dataset.bars]
    highs = [bar.high for bar in dataset.bars]
    lows = [bar.low for bar in dataset.bars]
    ema_fast = ema(closes, 12)
    ema_slow = ema(closes, 26)
    rsi_line = rsi(closes, 14)
    macd_line, signal_line = macd(closes)
    atr_line = atr(highs, lows, closes, 14)

    def row(index: int) -> dict[str, Decimal | None]:
        return {
            "close": closes[index],
            "ema_fast": ema_fast[index],
            "ema_slow": ema_slow[index],
            "rsi": rsi_line[index],
            "macd": macd_line[index],
            "signal": signal_line[index],
            "atr": atr_line[index],
        }

    current = row(-1)
    previous = row(-2) if len(closes) > 1 else None
    evidence: dict[str, dict[str, Any]] = {}
    for name in ("entry", "exit"):
        rule = strategy[name]
        needed = [rule["left"]] + ([rule["right"]] if isinstance(rule["right"], str) else [])
        ready = all(current.get(key) is not None for key in needed)
        if rule["op"].startswith("crosses_"):
            ready = ready and previous is not None and all(previous.get(key) is not None for key in needed)
        matched = evaluate(rule, current, previous) if ready else False  # type: ignore[arg-type]
        evidence[name] = {"rule": rule, "matched": matched, "ready": ready}
    strategy_hash = hashlib.sha256(json.dumps(strategy, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return Analysis(
        analysis_id, dataset.id, dataset.symbol, dataset.bars[-1].session.isoformat(),
        current, evidence, dataset.checksum, strategy_hash, "analysis-1", datetime.now(timezone.utc),
    )
