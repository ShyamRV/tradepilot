# Day-trader skill → TradePilot workflow notes

Source: [Jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill) (MIT).
We are **not** replacing TradePilot with that pack. We reuse a few durable ideas.

## Patterns worth keeping

1. **Pipeline, not a single “AI trade” button**  
   Scan / news / entry / exit / size / risk / explicit approve. TradePilot agents already start **paused**; keep that gate.
2. **Deterministic risk before LLM narrative**  
   Size and daily-loss checks stay in code. GLM (or any model) only explains evidence — matches ADR 0006.
3. **Budget from max loss**  
   Show capital vs daily stop as a clear budget check (wired into agent create UI).
4. **No silent execution**  
   User must Start / approve. Kill cannot rewrite history of fills.
5. **Paper default**  
   Aligns with `PAPER_TRADING=true` and sandbox broker.

## Explicitly not adopting (for now)

- Claude plugin / `SKILL.md` install path (we use GLM via OpenAI-compatible `LLMProvider` later).
- Full US Yahoo universe scanner, SEC/Pelosi modules, Alpaca MCP “Allow once” card.
- File-based `trader/*.json` workspace on disk — TradePilot uses API + DB / demo store.

## Implemented in TradePilot

- `packages/tradepilot/strategies/` — adapted scan / entry / exit / budget / timemachine / pipeline
- `packages/tradepilot/workers/agent_loop.py` — autonomous paper cycle for RUNNING delegated agents
- Agent create UI — day / swing / long-term templates; control room shows pipeline stage + odds
- GLM provider (`llm_glm.py`) — OpenAI-compatible; falls back when unset
