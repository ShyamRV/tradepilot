from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .bars import Bar, synthesize_session_bars
from .budget import size_from_max_loss
from .entry import EntryStatus, evaluate_entry
from .exit_plan import ExitPlan, plan_exit
from .scan import ScanHit, scan_bars
from .timemachine import TimeMachineResult, run_timemachine


@dataclass(frozen=True)
class PipelineResult:
    symbol: str
    horizon: str
    stage: str
    hits: tuple[ScanHit, ...]
    entry_status: str | None
    entry_price: Decimal | None
    plan: ExitPlan | None
    quantity: int
    odds: TimeMachineResult | None
    action: str
    rationale: dict[str, Any]
    indicators: tuple[dict[str, Any], ...]
    risk_checks: tuple[dict[str, Any], ...]


def evaluate_symbol(
    *,
    symbol: str,
    horizon: str,
    setups: tuple[str, ...],
    max_capital: Decimal,
    max_daily_loss: Decimal,
    daily_pnl: Decimal,
    seed: int,
    base_price: Decimal,
    stop_rule: str = "or_mid",
    target_r: Decimal = Decimal("1"),
    intraday_bars: tuple[Bar, ...] | None = None,
    history_sessions: list[tuple[Bar, ...]] | None = None,
    daily_closes: tuple[Decimal, ...] | None = None,
    require_odds_edge: bool = False,
) -> PipelineResult:
    """One autonomous evaluation cycle for a symbol (scan→entry→exit→size→odds)."""
    bars = intraday_bars or synthesize_session_bars(symbol=symbol, base_price=base_price, seed=seed)
    closes = daily_closes
    if closes is None:
        closes = tuple(
            synthesize_session_bars(symbol=symbol, base_price=base_price, seed=seed + day)[-1].close
            for day in range(60)
        )
    as_of = bars[-1].start.isoformat()
    if horizon == "intraday":
        active_setups = setups or ("orb", "breakout_20d", "bull_flag", "oversold_bounce")
    else:
        active_setups = setups or ("swing_ma50_reclaim", "breakout_20d", "reclaim_ma20")
    hits = scan_bars(symbol, intraday=bars if horizon == "intraday" else None, daily_closes=closes, as_of=as_of, setups=active_setups)
    if not hits:
        return PipelineResult(
            symbol,
            horizon,
            "scan",
            (),
            None,
            None,
            None,
            0,
            None,
            "hold",
            {"summary": "No setup matched scan rules.", "model_version": "strategy-pipeline-v1"},
            (),
            ({"code": "scan_hit", "passed": False},),
        )

    preferred = next((hit for hit in hits if hit.setup == "orb"), hits[0])
    entry_setup = "orb" if preferred.setup == "orb" else "level"
    level = None if entry_setup == "orb" else preferred.score
    entry = evaluate_entry(symbol, bars, setup=entry_setup, level=level)
    if entry.status != EntryStatus.TRIGGERED or entry.price is None:
        return PipelineResult(
            symbol,
            horizon,
            "entry",
            hits,
            entry.status.value,
            entry.price,
            None,
            0,
            None,
            "hold",
            {"summary": entry.message, "model_version": "strategy-pipeline-v1"},
            ({"setup": preferred.setup, "detail": preferred.detail},),
            ({"code": "entry_triggered", "passed": False}, {"code": "scan_hit", "passed": True}),
        )

    plan = plan_exit(
        symbol,
        entry=entry.price,
        bars=bars,
        stop_rule=stop_rule if horizon == "intraday" else ("pct" if stop_rule == "or_mid" else stop_rule),
        target_r=target_r if horizon == "intraday" else max(target_r, Decimal("2")),
        flat_by_bar=75 if horizon == "intraday" else None,
    )
    qty = size_from_max_loss(
        entry=plan.entry,
        stop=plan.stop,
        max_loss=max_daily_loss,
        max_capital=max_capital,
    )
    risk_checks = [
        {"code": "scan_hit", "passed": True},
        {"code": "entry_triggered", "passed": True},
        {"code": "quantity_positive", "passed": qty > 0},
        {"code": "daily_loss_room", "passed": daily_pnl > -max_daily_loss},
        {"code": "stop_below_entry", "passed": plan.stop < plan.entry},
    ]
    sessions = history_sessions or [
        synthesize_session_bars(symbol=symbol, base_price=base_price, seed=seed + 100 + day) for day in range(30)
    ]
    odds = run_timemachine(plan, sessions, entry_bar_index=entry.bar_index or 8, replays=500, seed=19)
    edge_ok = True
    if require_odds_edge and "coin flip" in odds.verdict.lower():
        edge_ok = False
        risk_checks.append({"code": "timemachine_edge", "passed": False})
    else:
        risk_checks.append({"code": "timemachine_edge", "passed": True})

    action = "buy" if qty > 0 and all(item["passed"] for item in risk_checks) and edge_ok else "hold"
    return PipelineResult(
        symbol,
        horizon,
        "ready" if action == "buy" else "blocked",
        hits,
        entry.status.value,
        entry.price,
        plan,
        qty,
        odds,
        action,
        {
            "summary": (
                f"{preferred.setup} on {symbol}: entry {plan.entry}, stop {plan.stop}, target {plan.target}, "
                f"qty {qty}. Time machine: {odds.verdict}."
            ),
            "model_version": "strategy-pipeline-v1",
            "odds": {
                "target_first_pct": str(odds.target_first_pct),
                "stop_first_pct": str(odds.stop_first_pct),
                "neither_pct": str(odds.neither_pct),
                "verdict": odds.verdict,
                "seed": odds.seed,
            },
        },
        (
            {"setup": preferred.setup, "detail": preferred.detail},
            {"entry": str(plan.entry), "stop": str(plan.stop), "target": str(plan.target)},
        ),
        tuple(risk_checks),
    )
