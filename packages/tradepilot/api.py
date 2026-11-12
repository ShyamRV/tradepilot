from __future__ import annotations

import asyncio
import os
import re
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from .ai import explain_record
from .agent_runtime import DeterministicAgentRuntime
from .agents import AgentConfig, AgentControlPlane
from .analysis import analyze
from .auth import AuthProvider, AuthenticationError, InMemoryAuthProvider
from .controls import BetaControls, FeatureDisabledError, QuotaExceededError
from .core import ForbiddenError, InMemoryRepository, OutboxMessage, Principal, Repository, audit, authorize
from .durable import build_runtime
from .execution import PaperLedger, backtest
from .logging_utils import configure_logging, init_sentry_stub
from .market import Bar, TradingCalendar, ingest
from .realtime import SandboxBroker, SimulatedMarketDataProvider
from .risk import PretradeContext, RiskLimits, evaluate_pretrade, position_size
from .settings import TradingSettings
from .strategy import TEMPLATES, validate_strategy
from .trading import BrokerGateway, MarketDataProvider, Order, OrderRequest, OrderStatus, OrderType, Side


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int = 120) -> None:
        super().__init__(app)
        self.limit = limit_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/ready"}:
            return await call_next(request)
        key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
        now = time.time()
        window = self.hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.limit:
            return JSONResponse(status_code=429, content={"detail": {"code": "rate_limited", "limit": self.limit}})
        window.append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response


class Credentials(BaseModel):
    email: str
    password: str


class WorkspaceInput(BaseModel):
    name: str


class MembershipInput(BaseModel):
    email: str
    role: str = "member"


class BarInput(BaseModel):
    session: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class DatasetInput(BaseModel):
    symbol: str
    idempotency_key: str
    bars: list[BarInput] = Field(min_length=1)


class StrategyInput(BaseModel):
    name: str
    spec: dict[str, Any]


class AnalysisInput(BaseModel):
    idempotency_key: str
    dataset_id: str
    strategy_name: str


class RiskInput(BaseModel):
    equity: Decimal
    entry: Decimal
    stop: Decimal


class NotificationInput(BaseModel):
    idempotency_key: str
    chat_id: str
    text: str = Field(min_length=1, max_length=4096)


class PaperOrderInput(BaseModel):
    idempotency_key: str
    dataset_id: str
    signal_session: date
    side: str
    quantity: int = Field(gt=0)


class WatchlistInput(BaseModel):
    symbol: str


class RealtimeOrderInput(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=20)
    side: Side
    quantity: int = Field(gt=0)
    order_type: OrderType = OrderType.MARKET
    limit_price: Decimal | None = Field(default=None, gt=0)
    equity: Decimal = Field(gt=0)
    cash: Decimal = Field(ge=0)
    daily_pnl: Decimal = Decimal("0")
    current_position: int = 0
    open_orders: int = Field(default=0, ge=0)
    agent_id: str | None = None


class AgentInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    symbols: list[str] = Field(min_length=1, max_length=100)
    strategy: str = Field(min_length=1, max_length=120)
    max_capital: Decimal = Field(gt=0)
    max_daily_loss: Decimal = Field(gt=0)


class AgentControlInput(BaseModel):
    action: str
    reason: str = Field(min_length=1, max_length=500)


class ExecutionControlInput(BaseModel):
    killed: bool
    reason: str = Field(min_length=1, max_length=500)


def create_app(
    repository: Repository | None = None,
    auth_provider: AuthProvider | None = None,
    controls: BetaControls | None = None,
    explanation_model: Callable[[str], dict[str, Any]] | None = None,
    explanation_model_version: str = "unconfigured",
    trading_settings: TradingSettings | None = None,
    market_data_provider: MarketDataProvider | None = None,
    broker_gateway: BrokerGateway | None = None,
) -> FastAPI:
    production = os.getenv("TRADEPILOT_ENV", "development").lower() == "production"
    if repository is None and auth_provider is None:
        repository, auth_provider = build_runtime()
    elif repository is None:
        repository = InMemoryRepository()
    if auth_provider is None:
        if production:
            raise RuntimeError("production requires a durable AuthProvider")
        auth_provider = InMemoryAuthProvider()
    if production and (
        isinstance(repository, InMemoryRepository) or isinstance(auth_provider, InMemoryAuthProvider)
    ):
        raise RuntimeError("production refuses InMemory repository or auth")
    repo = repository
    auth = auth_provider
    beta = controls or BetaControls()
    settings = trading_settings or TradingSettings.from_env()
    market_provider = market_data_provider or SimulatedMarketDataProvider(
        seed=settings.simulator_seed, spread_bps=settings.simulator_spread_bps
    )
    broker = broker_gateway or SandboxBroker(
        slippage_bps=settings.simulator_slippage_bps,
        max_fill_quantity=settings.simulator_max_fill_quantity,
    )
    if not broker.sandbox:
        raise RuntimeError("only a sandbox BrokerGateway is permitted")
    agent_control = AgentControlPlane(repo)
    agent_runtime = DeterministicAgentRuntime()
    model_call = explanation_model or (lambda _: {})

    def execution_control(workspace_id: str) -> dict[str, Any]:
        stored = repo.get("execution_controls", workspace_id, "workspace")
        return stored or {
            "scope": "workspace",
            "killed": settings.global_execution_kill,
            "reason": "global environment kill" if settings.global_execution_kill else "not killed",
            "version": 0,
        }
    configure_logging("api")
    init_sentry_stub()
    app = FastAPI(title="TradePilot API", version="0.3.0")
    origins = [item.strip() for item in os.getenv("TRADEPILOT_CORS_ORIGINS", "http://localhost:3000").split(",") if item.strip()]
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, limit_per_minute=int(os.getenv("TRADEPILOT_RATE_LIMIT_PER_MINUTE", "120")))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Workspace-ID", "Idempotency-Key"],
    )
    app.state.repository, app.state.auth_provider, app.state.controls = repo, auth, beta
    app.state.trading_settings = settings
    app.state.market_data_provider = market_provider
    app.state.broker_gateway = broker

    def bearer(authorization: str = Header(...)) -> str:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthenticationError("bearer session required")
        return token

    def principal(
        token: str = Depends(bearer),
        x_workspace_id: str = Header(...),
    ) -> Principal:
        return auth.principal(token, x_workspace_id)

    @app.exception_handler(AuthenticationError)
    async def authentication_error(_, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden(_, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def bad_request(_, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(QuotaExceededError)
    async def quota_exceeded(_, exc: QuotaExceededError):
        return JSONResponse(
            status_code=429,
            content={"detail": {"code": "quota_exceeded", "quota": exc.quota, "limit": exc.limit}},
        )

    @app.exception_handler(FeatureDisabledError)
    async def feature_disabled(_, exc: FeatureDisabledError):
        return JSONResponse(
            status_code=503,
            content={"detail": {"code": "feature_disabled", "feature": exc.feature}},
        )

    def today_count(bucket: str, workspace_id: str) -> int:
        today = datetime.now(timezone.utc).date()
        return sum(
            1
            for item in repo.values(bucket, workspace_id)
            if (item.created_at if hasattr(item, "created_at") else item["created_at"]).date() == today
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "tradepilot-api"}

    @app.get("/ready")
    def ready():
        checks: dict[str, str] = {"app": "ok"}
        ping = getattr(repo, "ping", None)
        if callable(ping):
            try:
                ping()
                checks["repository"] = "ok"
            except Exception as exc:  # pragma: no cover
                return JSONResponse(
                    status_code=503,
                    content={"status": "not_ready", "checks": {"repository": "error"}, "detail": str(exc)},
                )
        else:
            checks["repository"] = "in_memory"
        if (os.getenv("DATABASE_URL") or "").strip():
            checks["database_url"] = "configured"
        elif (os.getenv("TRADEPILOT_DB_PATH") or "").strip():
            checks["db_path"] = "configured"
        else:
            checks["database_url"] = "unconfigured"
        return {"status": "ready", "checks": checks}

    @app.post("/v1/auth/register", status_code=201)
    def register(body: Credentials):
        return auth.register(body.email, body.password)

    @app.post("/v1/auth/login")
    def login(body: Credentials):
        return {"access_token": auth.login(body.email, body.password), "token_type": "bearer"}

    @app.post("/v1/auth/logout", status_code=204)
    def logout(token: str = Depends(bearer)):
        auth.logout(token)

    @app.post("/v1/workspaces", status_code=201)
    def create_workspace(body: WorkspaceInput, token: str = Depends(bearer)):
        return auth.create_workspace(token, body.name)

    @app.get("/v1/workspaces")
    def list_workspaces(token: str = Depends(bearer)):
        return [{"workspace": workspace, "role": role} for workspace, role in auth.workspaces(token)]

    @app.post("/v1/workspaces/{workspace_id}/members", status_code=204)
    def add_member(workspace_id: str, body: MembershipInput, token: str = Depends(bearer), actor: Principal = Depends(principal)):
        authorize(actor, workspace_id, "owner")
        auth.add_member(token, workspace_id, body.email, body.role)

    @app.get("/v1/strategy-templates")
    def templates():
        return TEMPLATES

    @app.post("/v1/workspaces/{workspace_id}/watchlist", status_code=201)
    def add_watchlist_item(workspace_id: str, body: WatchlistInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        symbol = body.symbol.strip().upper()
        if not re.fullmatch(r"[A-Z0-9&-]{1,20}", symbol):
            raise ValueError("invalid stable symbol")
        existing = repo.get("watchlist", workspace_id, symbol)
        if existing:
            return existing
        beta.require_quota(workspace_id, "watchlist_items", len(repo.values("watchlist", workspace_id)))
        record = {"symbol": symbol, "created_at": datetime.now(timezone.utc)}
        repo.put("watchlist", workspace_id, symbol, record)
        audit(repo, actor, "watchlist.added", symbol)
        return record

    @app.get("/v1/workspaces/{workspace_id}/watchlist")
    def list_watchlist(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("watchlist", workspace_id)

    @app.delete("/v1/workspaces/{workspace_id}/watchlist/{symbol}", status_code=204)
    def delete_watchlist_item(workspace_id: str, symbol: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        stable = symbol.strip().upper()
        if not repo.delete("watchlist", workspace_id, stable):
            raise HTTPException(404, "watchlist item not found")
        audit(repo, actor, "watchlist.removed", stable)

    @app.post("/v1/workspaces/{workspace_id}/datasets", status_code=201)
    def create_dataset(workspace_id: str, body: DatasetInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        dataset = ingest(body.symbol, (Bar(**bar.model_dump()) for bar in body.bars), body.idempotency_key)
        existing = repo.get("datasets", workspace_id, dataset.id)
        if existing:
            return existing
        repo.put("datasets", workspace_id, dataset.id, dataset)
        audit(repo, actor, "dataset.ingested", dataset.id, checksum=dataset.checksum)
        return dataset

    @app.get("/v1/workspaces/{workspace_id}/datasets")
    def list_datasets(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("datasets", workspace_id)

    @app.post("/v1/workspaces/{workspace_id}/datasets/{dataset_id}/publish")
    def publish_dataset(workspace_id: str, dataset_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id, "publisher")
        beta.require_feature(workspace_id, "dataset_publication")
        dataset = repo.get("datasets", workspace_id, dataset_id)
        if not dataset:
            raise HTTPException(404, "dataset not found")
        published = dataset.publish()
        repo.replace("datasets", workspace_id, dataset_id, published)
        audit(repo, actor, "dataset.published", dataset_id)
        return published

    @app.post("/v1/workspaces/{workspace_id}/strategies", status_code=201)
    def create_strategy(workspace_id: str, body: StrategyInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        record = {"name": body.name, "spec": validate_strategy(body.spec)}
        existing = repo.get("strategies", workspace_id, body.name)
        if existing:
            return existing
        beta.require_quota(workspace_id, "strategies", len(repo.values("strategies", workspace_id)))
        repo.put("strategies", workspace_id, body.name, record)
        audit(repo, actor, "strategy.created", body.name)
        return record

    @app.get("/v1/workspaces/{workspace_id}/strategies")
    def list_strategies(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("strategies", workspace_id)

    @app.post("/v1/workspaces/{workspace_id}/analyses", status_code=201)
    def create_analysis(workspace_id: str, body: AnalysisInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        beta.require_feature(workspace_id, "analysis")
        existing = repo.get("analyses", workspace_id, body.idempotency_key)
        if existing:
            return existing
        beta.require_quota(workspace_id, "analyses_per_day", today_count("analyses", workspace_id))
        dataset = repo.get("datasets", workspace_id, body.dataset_id)
        strategy = repo.get("strategies", workspace_id, body.strategy_name)
        if not dataset or not strategy:
            raise HTTPException(404, "dataset or strategy not found")
        result = analyze(dataset, strategy["spec"], body.idempotency_key)
        repo.put("analyses", workspace_id, result.id, result)
        audit(repo, actor, "analysis.created", result.id, dataset_id=result.dataset_id)
        return result

    @app.get("/v1/workspaces/{workspace_id}/analyses")
    def list_analyses(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("analyses", workspace_id)

    @app.post("/v1/workspaces/{workspace_id}/analyses/{analysis_id}/explanation", status_code=201)
    def create_explanation(workspace_id: str, analysis_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        beta.require_feature(workspace_id, "ai_explanation")
        existing = repo.get("explanations", workspace_id, analysis_id)
        if existing:
            return existing
        analysis = repo.get("analyses", workspace_id, analysis_id)
        if not analysis:
            raise HTTPException(404, "analysis not found")
        signal = "entry" if analysis.evidence["entry"]["matched"] else "exit" if analysis.evidence["exit"]["matched"] else "neutral"
        record = explain_record(
            analysis.id,
            {
                "symbol": analysis.symbol,
                "signal": signal,
                "indicators": analysis.indicators,
                "session": analysis.session,
            },
            model_call,
            model_version=explanation_model_version,
        )
        repo.put("explanations", workspace_id, analysis_id, record)
        audit(repo, actor, "explanation.created", analysis_id, fallback=record.fallback)
        return record

    @app.post("/v1/workspaces/{workspace_id}/risk/position-size")
    def size(workspace_id: str, body: RiskInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return {"quantity": position_size(body.equity, body.entry, body.stop, RiskLimits())}

    @app.post("/v1/workspaces/{workspace_id}/backtests/{dataset_id}")
    def run_backtest(workspace_id: str, dataset_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        beta.require_quota(workspace_id, "backtests_per_day", today_count("backtests", workspace_id))
        dataset = repo.get("datasets", workspace_id, dataset_id)
        if not dataset:
            raise HTTPException(404, "dataset not found")
        result = backtest(dataset, {"template": "buy_once"}, lambda i, _: "buy" if i == 0 else None)
        run_id = f"{dataset_id}:{datetime.now(timezone.utc).isoformat()}"
        repo.put("backtests", workspace_id, run_id, {"id": run_id, "created_at": datetime.now(timezone.utc), "result": result})
        audit(repo, actor, "backtest.completed", dataset_id, fills=len(result.fills))
        return result

    @app.post("/v1/workspaces/{workspace_id}/paper/orders", status_code=201)
    def create_paper_order(workspace_id: str, body: PaperOrderInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        existing = repo.get("paper_orders", workspace_id, body.idempotency_key)
        if existing:
            return existing
        dataset = repo.get("datasets", workspace_id, body.dataset_id)
        if not dataset or dataset.status != "published":
            raise HTTPException(404, "published dataset not found")
        fill_session = TradingCalendar().next_session(body.signal_session)
        fill_bar = next((bar for bar in dataset.bars if bar.session == fill_session), None)
        if not fill_bar:
            raise ValueError("next-session market data unavailable")
        ledger = repo.get("paper_ledgers", workspace_id, "default")
        created_ledger = False
        if ledger is None:
            ledger = PaperLedger()
            created_ledger = True
        fill = ledger.fill(body.idempotency_key, dataset.symbol, fill_session, body.side, body.quantity, fill_bar.open)
        if created_ledger:
            repo.put("paper_ledgers", workspace_id, "default", ledger)
        else:
            repo.replace("paper_ledgers", workspace_id, "default", ledger)
        record = {"id": body.idempotency_key, "dataset_id": body.dataset_id, "signal_session": body.signal_session, "fill": fill}
        repo.put("paper_orders", workspace_id, body.idempotency_key, record)
        audit(repo, actor, "paper_order.filled", body.idempotency_key)
        return record

    @app.get("/v1/workspaces/{workspace_id}/paper/orders")
    def list_paper_orders(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("paper_orders", workspace_id)

    @app.get("/v1/workspaces/{workspace_id}/market/quotes/{symbol}")
    def realtime_quote(workspace_id: str, symbol: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return market_provider.quote(symbol)

    @app.websocket("/v1/workspaces/{workspace_id}/market/stream/{symbol}")
    async def market_stream(websocket: WebSocket, workspace_id: str, symbol: str):
        token = websocket.query_params.get("token", "")
        try:
            actor = auth.principal(token, workspace_id)
            authorize(actor, workspace_id)
        except (AuthenticationError, ForbiddenError):
            await websocket.close(code=4401)
            return
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(jsonable_encoder(market_provider.quote(symbol)))
                await asyncio.sleep(0.25)
        except WebSocketDisconnect:
            return

    @app.post("/v1/workspaces/{workspace_id}/sandbox/orders", status_code=201)
    def create_sandbox_order(
        workspace_id: str, body: RealtimeOrderInput, actor: Principal = Depends(principal)
    ):
        authorize(actor, workspace_id)
        existing = repo.get("sandbox_orders", workspace_id, body.idempotency_key)
        if existing:
            return existing
        active_agent = None
        if body.agent_id:
            agent = agent_control.get(workspace_id, body.agent_id)
            if agent is None:
                raise HTTPException(404, "agent not found")
            if not settings.autonomous_trading_enabled:
                raise HTTPException(503, {"code": "autonomous_trading_disabled"})
            if agent.status != "running":
                raise ValueError("agent is not running")
            if body.symbol.strip().upper() not in agent.config.symbols:
                raise ValueError("symbol is outside agent universe")
            if body.equity > agent.config.max_capital or -body.daily_pnl >= agent.config.max_daily_loss:
                raise ValueError("agent capital guardrail breached")
            active_agent = agent
        request = OrderRequest(
            id=body.idempotency_key,
            workspace_id=workspace_id,
            symbol=body.symbol.strip().upper(),
            side=body.side,
            quantity=body.quantity,
            order_type=body.order_type,
            limit_price=body.limit_price,
            agent_id=body.agent_id,
        )
        quote = market_provider.quote(request.symbol)
        decision = evaluate_pretrade(
            request,
            quote,
            PretradeContext(body.equity, body.cash, body.daily_pnl, body.current_position, body.open_orders),
        )
        repo.put("risk_decisions", workspace_id, request.id, decision)
        audit(
            repo, actor, "risk.evaluated", request.id,
            outcome=decision.outcome.value, reasons=list(decision.reasons), formula=decision.formula_version,
        )
        if decision.allowed:
            control = execution_control(workspace_id)
            if control["killed"]:
                order = Order(request).transition(OrderStatus.REJECTED, reason="execution_killed")
            elif not settings.broker_execution_enabled:
                order = Order(request).transition(OrderStatus.REJECTED, reason="broker_execution_disabled")
            else:
                order = broker.submit(request, quote)
        else:
            order = Order(request).transition(OrderStatus.RISK_REJECTED, reason=",".join(decision.reasons))
        repo.put("sandbox_orders", workspace_id, request.id, order)
        if active_agent is not None:
            trace = agent_runtime.decide(
                agent_id=active_agent.id,
                signal={"symbol": request.symbol, "side": request.side.value, "source": "strategy"},
                indicators=(),
                risk_checks=tuple(
                    {"code": reason, "passed": False} for reason in decision.reasons
                ) or ({"code": "pretrade", "passed": True},),
                authority_version=active_agent.updated_at.isoformat(),
                resulting_order_id=request.id,
            )
            repo.put("agent_decisions", workspace_id, trace.id, trace)
        audit(
            repo, actor, "sandbox_order.created", request.id,
            status=order.status.value, agent_id=body.agent_id, broker=broker.name,
        )
        return order

    @app.get("/v1/workspaces/{workspace_id}/sandbox/orders")
    def list_sandbox_orders(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("sandbox_orders", workspace_id)

    @app.post("/v1/workspaces/{workspace_id}/sandbox/orders/{order_id}/cancel")
    def cancel_sandbox_order(workspace_id: str, order_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        existing = repo.get("sandbox_orders", workspace_id, order_id)
        if existing is None:
            raise HTTPException(404, "order not found")
        try:
            order = broker.cancel(order_id)
        except (KeyError, ValueError) as exc:
            raise HTTPException(409, str(exc)) from None
        repo.replace("sandbox_orders", workspace_id, order_id, order)
        audit(repo, actor, "sandbox_order.cancelled", order_id, status=order.status.value)
        return order

    @app.get("/v1/workspaces/{workspace_id}/execution/control")
    def get_execution_control(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return execution_control(workspace_id)

    @app.put("/v1/workspaces/{workspace_id}/execution/control")
    def set_execution_control(
        workspace_id: str, body: ExecutionControlInput, actor: Principal = Depends(principal)
    ):
        authorize(actor, workspace_id, "owner")
        current = execution_control(workspace_id)
        record = {
            "scope": "workspace",
            "killed": body.killed,
            "reason": body.reason,
            "version": int(current["version"]) + 1,
            "updated_at": datetime.now(timezone.utc),
        }
        if current["version"] == 0 and repo.get("execution_controls", workspace_id, "workspace") is None:
            repo.put("execution_controls", workspace_id, "workspace", record)
        else:
            repo.replace("execution_controls", workspace_id, "workspace", record)
        if body.killed:
            for agent in agent_control.list(workspace_id):
                if agent.status.value not in {"killed", "stopped"}:
                    try:
                        agent_control.control(workspace_id, agent.id, "pause", f"execution kill: {body.reason}")
                    except ValueError:
                        pass
        audit(repo, actor, "execution.killed" if body.killed else "execution.resumed", "workspace", **record)
        return record

    @app.post("/v1/workspaces/{workspace_id}/agents", status_code=201)
    def create_agent(workspace_id: str, body: AgentInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id, "owner")
        symbols = tuple(dict.fromkeys(symbol.strip().upper() for symbol in body.symbols if symbol.strip()))
        agent = agent_control.create(
            workspace_id,
            AgentConfig(body.name, symbols, body.strategy, body.max_capital, body.max_daily_loss),
        )
        audit(repo, actor, "agent.created", agent.id)
        return agent

    @app.get("/v1/workspaces/{workspace_id}/agents")
    def list_agents(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return agent_control.list(workspace_id)

    @app.get("/v1/workspaces/{workspace_id}/agents/{agent_id}/decisions")
    def list_agent_decisions(workspace_id: str, agent_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        if agent_control.get(workspace_id, agent_id) is None:
            raise HTTPException(404, "agent not found")
        return tuple(
            decision
            for decision in repo.values("agent_decisions", workspace_id)
            if decision.agent_id == agent_id
        )

    @app.post("/v1/workspaces/{workspace_id}/agents/{agent_id}/control")
    def control_agent(
        workspace_id: str,
        agent_id: str,
        body: AgentControlInput,
        actor: Principal = Depends(principal),
    ):
        authorize(actor, workspace_id, "owner")
        if body.action in {"start", "resume"} and not settings.autonomous_trading_enabled:
            raise HTTPException(503, {"code": "autonomous_trading_disabled"})
        if body.action in {"start", "resume"} and execution_control(workspace_id)["killed"]:
            raise HTTPException(503, {"code": "execution_killed"})
        try:
            agent = agent_control.control(workspace_id, agent_id, body.action, body.reason)
        except KeyError:
            raise HTTPException(404, "agent not found") from None
        audit(repo, actor, f"agent.{body.action}", agent.id, reason=body.reason, status=agent.status.value)
        return agent

    @app.post("/v1/workspaces/{workspace_id}/notifications", status_code=202)
    def notify(workspace_id: str, body: NotificationInput, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        beta.require_feature(workspace_id, "notification_dispatch")
        existing = repo.get("notifications", workspace_id, body.idempotency_key)
        if existing:
            return {"id": existing.id, "created": False}
        beta.require_quota(workspace_id, "notifications_per_day", today_count("notifications", workspace_id))
        message = OutboxMessage(body.idempotency_key, workspace_id, "telegram", body.model_dump(exclude={"idempotency_key"}), datetime.now(timezone.utc))
        created = repo.enqueue(message)
        if created:
            repo.put("notifications", workspace_id, message.id, message)
            audit(repo, actor, "notification.enqueued", message.id)
        return {"id": message.id, "created": created}

    @app.get("/v1/workspaces/{workspace_id}/notifications")
    def list_notifications(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id)
        return repo.values("notifications", workspace_id)

    @app.get("/v1/workspaces/{workspace_id}/audit")
    def list_audit(workspace_id: str, actor: Principal = Depends(principal)):
        authorize(actor, workspace_id, "auditor")
        return repo.audits(workspace_id)

    @app.get("/v1/workspaces/{workspace_id}/dashboard")
    def dashboard(
        workspace_id: str,
        actor: Principal = Depends(principal),
        token: str = Depends(bearer),
    ):
        authorize(actor, workspace_id)
        ledger = repo.get("paper_ledgers", workspace_id, "default")
        datasets = repo.values("datasets", workspace_id)
        strategies = repo.values("strategies", workspace_id)
        analyses = repo.values("analyses", workspace_id)
        notifications = repo.values("notifications", workspace_id)
        workspace = next(item for item, _ in auth.workspaces(token) if item.id == workspace_id)
        published_datasets = tuple(item for item in datasets if item.status == "published")
        latest_dataset = max(published_datasets, key=lambda item: item.created_at, default=None)
        latest_analysis = max(analyses, key=lambda item: item.created_at, default=None)
        as_of = latest_dataset.bars[-1].session.isoformat() if latest_dataset else ""
        updated_at = (
            latest_analysis.created_at.isoformat()
            if latest_analysis
            else latest_dataset.created_at.isoformat() if latest_dataset else ""
        )
        rules = []
        if latest_analysis:
            rules = [
                {
                    "label": name,
                    "result": "pass" if evidence["matched"] else "fail",
                    "evidence": "Rule matched recorded inputs." if evidence["matched"] else "Rule did not match or indicators were warming up.",
                }
                for name, evidence in latest_analysis.evidence.items()
            ]
        fills = ledger.fills if ledger else []
        dashboard_watchlist = []
        for item in repo.values("watchlist", workspace_id):
            candidates = [
                dataset for dataset in published_datasets if dataset.symbol == item["symbol"]
            ]
            if not candidates:
                continue
            priced = max(candidates, key=lambda dataset: dataset.created_at)
            last, previous = priced.bars[-1], priced.bars[-2] if len(priced.bars) > 1 else None
            change = ((last.close - previous.close) / previous.close * Decimal("100")) if previous else Decimal("0")
            related = [value for value in analyses if value.symbol == item["symbol"]]
            signal = ""
            if related:
                recent = max(related, key=lambda value: value.created_at)
                signal = "Entry" if recent.evidence["entry"]["matched"] else "Exit" if recent.evidence["exit"]["matched"] else "No signal"
            dashboard_watchlist.append(
                {"symbol": item["symbol"], "price": last.close, "change": change, "signal": signal}
            )
        return {
            "workspace": {"name": workspace.name, "market": "NSE cash equities", "mode": "Paper trading", "updatedAt": updated_at},
            "freshness": {"status": "eod", "asOf": as_of, "delay": "End-of-day dataset" if latest_dataset else "No dataset"},
            "watchlist": dashboard_watchlist,
            "strategies": [
                {"id": item["name"], "name": item["name"], "description": "", "enabled": True, "settings": ""}
                for item in strategies
            ],
            "analysis": {
                "symbol": latest_analysis.symbol if latest_analysis else "",
                "verdict": "Entry" if latest_analysis and latest_analysis.evidence["entry"]["matched"] else "No signal",
                "confidence": 0,
                "rules": rules,
            },
            "risk": {"decision": "Blocked", "maxPosition": 0, "riskPerTrade": 0, "notes": ["No dashboard risk request recorded."]},
            "portfolio": {
                "cash": ledger.cash if ledger else 0,
                "equity": ledger.cash if ledger else 0,
                "pnl": 0,
                "positions": [],
            },
            "history": [
                {
                    "date": fill.session.isoformat(), "symbol": fill.symbol, "side": fill.side.title(),
                    "quantity": fill.quantity, "price": fill.price, "status": "Filled",
                }
                for fill in fills
            ],
            "backtest": {"returnPct": 0, "benchmarkPct": 0, "maxDrawdownPct": 0, "winRatePct": 0, "trades": 0},
            "notifications": [
                {
                    "id": item.id, "title": item.payload["text"], "detail": "",
                    "time": item.created_at.isoformat(), "level": "info",
                }
                for item in notifications
            ],
            "metadata": {
                "source": "Published workspace datasets" if latest_dataset else "No dataset",
                "asOf": as_of,
                "adjustment": "As supplied by the dataset provider",
                "limitations": "Empty and zero values mean no corresponding persisted record; no market facts are fabricated.",
            },
        }

    @app.get("/api/dashboard")
    def selected_dashboard(
        actor: Principal = Depends(principal),
        token: str = Depends(bearer),
    ):
        return dashboard(actor.workspace_id, actor, token)

    return app
