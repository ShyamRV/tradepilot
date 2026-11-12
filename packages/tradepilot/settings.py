from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


def _boolean(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false", "1", "0", "yes", "no"}:
        raise ValueError(f"invalid boolean setting: {value}")
    return normalized in {"true", "1", "yes"}


@dataclass(frozen=True)
class TradingSettings:
    market_data_provider: str = "simulated"
    broker_provider: str = "sandbox"
    broker_environment: str = "sandbox"
    paper_trading: bool = True
    broker_execution_enabled: bool = False
    autonomous_trading_enabled: bool = False
    global_execution_kill: bool = False
    live_execution_enabled: bool = False
    simulator_seed: int = 7
    simulator_spread_bps: Decimal = Decimal("5")
    simulator_slippage_bps: Decimal = Decimal("2")
    simulator_max_fill_quantity: int = 25

    def __post_init__(self) -> None:
        if not self.paper_trading:
            raise ValueError("this release requires PAPER_TRADING=true")
        if self.live_execution_enabled:
            raise ValueError("live execution is unavailable; use the sandbox broker")
        if self.broker_environment != "sandbox":
            raise ValueError("only BROKER_ENVIRONMENT=sandbox is permitted")
        if self.broker_provider != "sandbox":
            raise ValueError("only the sandbox broker is permitted")
        if self.simulator_seed < 0 or self.simulator_spread_bps < 0 or self.simulator_slippage_bps < 0:
            raise ValueError("simulator settings cannot be negative")
        if self.simulator_max_fill_quantity <= 0:
            raise ValueError("simulator max fill quantity must be positive")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "TradingSettings":
        env = environ or os.environ
        return cls(
            market_data_provider=env.get("MARKET_DATA_PROVIDER", "simulated").strip().lower(),
            broker_provider=env.get("BROKER_PROVIDER", "sandbox").strip().lower(),
            broker_environment=env.get("BROKER_ENVIRONMENT", "sandbox").strip().lower(),
            paper_trading=_boolean(env.get("PAPER_TRADING"), True),
            broker_execution_enabled=_boolean(env.get("BROKER_EXECUTION_ENABLED"), False),
            autonomous_trading_enabled=_boolean(env.get("AUTONOMOUS_TRADING_ENABLED"), False),
            global_execution_kill=_boolean(env.get("GLOBAL_EXECUTION_KILL"), False),
            live_execution_enabled=_boolean(env.get("LIVE_EXECUTION_ENABLED"), False),
            simulator_seed=int(env.get("SIMULATOR_SEED", "7")),
            simulator_spread_bps=Decimal(env.get("SIMULATOR_SPREAD_BPS", "5")),
            simulator_slippage_bps=Decimal(env.get("SIMULATOR_SLIPPAGE_BPS", "2")),
            simulator_max_fill_quantity=int(env.get("SIMULATOR_MAX_FILL_QUANTITY", "25")),
        )
