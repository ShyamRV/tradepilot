from __future__ import annotations

from decimal import Decimal

from tradepilot.strategies.bars import synthesize_session_bars
from tradepilot.strategies.budget import size_from_max_loss
from tradepilot.strategies.entry import EntryStatus, evaluate_entry
from tradepilot.strategies.exit_plan import plan_exit
from tradepilot.strategies.pipeline import evaluate_symbol
from tradepilot.strategies.scan import scan_orb
from tradepilot.strategies.timemachine import run_timemachine


def test_orb_scan_and_entry_trigger_on_synthesized_breakout():
    bars = synthesize_session_bars(symbol="TSLA", base_price=Decimal("360"), seed=7)
    hit = scan_orb("TSLA", bars, as_of="test")
    assert hit is not None
    assert hit.setup == "orb"
    entry = evaluate_entry("TSLA", bars, setup="orb")
    assert entry.status == EntryStatus.TRIGGERED
    assert entry.price is not None


def test_exit_budget_and_timemachine_produce_verdict():
    bars = synthesize_session_bars(symbol="TSLA", base_price=Decimal("360"), seed=7)
    entry = evaluate_entry("TSLA", bars, setup="orb")
    assert entry.price is not None
    plan = plan_exit("TSLA", entry=entry.price, bars=bars, stop_rule="or_mid", target_r=Decimal("1"))
    assert plan.stop < plan.entry < plan.target
    qty = size_from_max_loss(
        entry=plan.entry, stop=plan.stop, max_loss=Decimal("50"), max_capital=Decimal("5000")
    )
    assert qty >= 1
    sessions = [synthesize_session_bars(symbol="TSLA", base_price=Decimal("360"), seed=100 + day) for day in range(25)]
    odds = run_timemachine(plan, sessions, entry_bar_index=entry.bar_index or 8, replays=200, seed=19)
    assert odds.replays == 200
    assert odds.verdict


def test_evaluate_symbol_intraday_can_ready_buy():
    result = evaluate_symbol(
        symbol="RELIANCE",
        horizon="intraday",
        setups=("orb",),
        max_capital=Decimal("250000"),
        max_daily_loss=Decimal("5000"),
        daily_pnl=Decimal("0"),
        seed=7,
        base_price=Decimal("1532"),
    )
    assert result.hits
    assert result.action in {"buy", "hold"}
    if result.action == "buy":
        assert result.quantity > 0
        assert result.plan is not None
        assert result.odds is not None
