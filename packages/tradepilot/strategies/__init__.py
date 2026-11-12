"""Day-trader-skill inspired strategy primitives (adapted for TradePilot).

Original pack: https://github.com/Jakeschincariol/day-trader-skill (MIT).
These modules are deterministic libraries — not Claude skills — and never place
orders themselves. The agent loop + sandbox broker own execution.
"""

from .budget import size_from_max_loss
from .entry import EntryStatus, evaluate_entry
from .exit_plan import ExitPlan, plan_exit
from .pipeline import PipelineResult, evaluate_symbol
from .scan import ScanHit, scan_bars
from .timemachine import TimeMachineResult, run_timemachine

__all__ = [
    "EntryStatus",
    "ExitPlan",
    "PipelineResult",
    "ScanHit",
    "TimeMachineResult",
    "evaluate_entry",
    "evaluate_symbol",
    "plan_exit",
    "run_timemachine",
    "scan_bars",
    "size_from_max_loss",
]
