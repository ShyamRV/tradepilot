# TradePilot AI --- Complete Product & Business Concept

**Product category:** Modular AI trading intelligence platform\
**Business model:** SaaS subscriptions, white-label licensing, and
enterprise deployments\
**Positioning:** Your Markets. Your Strategy. Your AI Trading Partner.

------------------------------------------------------------------------

## 1. Executive Summary

TradePilot AI is a configurable AI-powered trading assistant designed to
help independent traders analyse markets, evaluate their own strategies,
understand risk, test ideas against historical data, and receive
personalised alerts.

The product is not intended to be a single-purpose trading bot. It is a
modular platform with a shared core engine and customer-specific
configurations. Each customer can choose supported markets, data
providers, trading styles, indicators, strategy rules, risk limits, and
notification channels without requiring a separate codebase.

The initial release should focus on read-only market intelligence,
strategy analysis, deterministic risk calculations, and paper trading.
Real-money execution should remain outside the MVP and only be
considered after legal, regulatory, broker, exchange, security, and
operational requirements have been assessed.

### Product vision

Build one adaptable trading intelligence platform that can serve: -
Individual traders. - Trading educators and communities. - Trading
groups. - Businesses seeking a white-label trading analytics product.

### Core value proposition

TradePilot AI brings market data, technical analysis, strategy
evaluation, risk calculations, explanations, and alerts into one
configurable workspace.

It helps traders make more informed decisions. It does not promise
profits, predict markets with certainty, or guarantee successful trades.

------------------------------------------------------------------------

## 2. Problem Statement

Independent traders often rely on multiple disconnected tools:

-   Charting platforms for price action and indicators.
-   Separate websites for market news and economic events.
-   Spreadsheets for journaling and performance tracking.
-   Manual calculations for position sizing and risk.
-   Messaging groups for trading discussions and alerts.
-   Personal scripts or indicator configurations for their strategies.

This creates fragmented workflows, repetitive analysis, and difficulty
consistently evaluating trading decisions.

TradePilot AI aims to reduce this friction by providing a single
configurable assistant that works with a trader's selected market,
strategy rules, risk preferences, and workflow.

------------------------------------------------------------------------

## 3. Target Customers

### 3.1 Individual traders

-   Crypto traders.
-   Forex traders.
-   Indian equity traders.
-   US equity traders.
-   Intraday traders.
-   Swing traders.
-   Positional traders.
-   Traders who use custom indicator combinations.

### 3.2 Trading educators and communities

-   Trading course creators.
-   Telegram and Discord trading communities.
-   Independent trading educators.
-   Paid trading groups.
-   Financial content creators.

### 3.3 Businesses

-   Trading analytics providers.
-   Fintech companies.
-   Broker or platform partners, subject to applicable permissions.
-   Businesses seeking private or white-label deployments.

### Initial ideal customer profile

Start with active independent traders who already use charts,
indicators, and trading rules. They understand the workflow and can
provide useful feedback on data accuracy, analysis quality, usability,
and alert relevance.

------------------------------------------------------------------------

## 4. Product Capabilities

TradePilot AI is organised around six core modules.

### 4.1 AI Market Analyst

Responsibilities: - Retrieve market data from configured providers. -
Analyse price and volume behaviour. - Calculate technical indicators. -
Identify conditions that match configured strategies. - Summarise trend,
momentum, volatility, and market structure. - Explain the evidence
behind a potential setup.

Example indicators: - EMA and SMA. - RSI. - MACD. - ATR. - VWAP. -
Bollinger Bands. - Volume moving averages.

The module should distinguish between observed data, calculated
indicators, and interpretation. It must display the data source and
timestamp.

### 4.2 News Intelligence

Responsibilities: - Retrieve relevant market news from permitted
sources. - Track scheduled economic events where supported. - Summarise
relevant developments. - Categorise possible relevance to configured
assets. - Link to original sources and display publication times.

News sentiment should be presented as contextual information, not as a
guaranteed predictor of price movements.

### 4.3 Risk Manager

Responsibilities: - Calculate position size from user-supplied account
and risk parameters. - Calculate risk-to-reward ratios. - Estimate
stop-loss distance and exposure. - Check configured daily loss and
open-position limits. - Flag incomplete or inconsistent trade inputs. -
Enforce deterministic risk constraints in paper-trading workflows.

Risk calculations must be performed by validated code, not improvised by
an LLM.

### 4.4 Strategy Lab

Responsibilities: - Create and manage strategy definitions. - Configure
indicators and rule conditions. - Validate strategy inputs. - Run
historical backtests. - Compare strategy versions. - Report performance
metrics and assumptions. - Support paper-trading evaluation.

Backtests should account for fees, slippage, data quality, look-ahead
bias, survivorship bias where relevant, and realistic execution
assumptions. Historical results do not guarantee future results.

### 4.5 Trading Companion

Responsibilities: - Answer questions about supported assets and
analysis. - Explain why a strategy condition did or did not trigger. -
Summarise watchlists. - Provide daily or periodic reports. - Send
user-configured alerts. - Help users understand their paper-trading
history.

### 4.6 Notification and Reporting

Initial channels: - Web dashboard. - Telegram bot. - Email may be added
later.

Users should control alert frequency, quiet hours, watchlists, and event
types to avoid excessive notifications.

------------------------------------------------------------------------

## 5. User Journey

### Step 1 --- Account creation

A user creates an account and receives a private workspace.

### Step 2 --- Trader profile

The user configures: - Preferred market. - Data provider or exchange. -
Assets and watchlists. - Trading style. - Timeframes. - Indicators. -
Strategy rules. - Risk preferences. - Notification channels. - Trading
mode.

### Step 3 --- Agent configuration

The platform creates a validated configuration for that user. Changes
are versioned and audited.

### Step 4 --- Market analysis

The system retrieves data, validates it, calculates indicators,
evaluates strategy rules, and checks risk constraints.

### Step 5 --- AI explanation

The LLM receives structured, validated outputs and explains them in
natural language. It must not invent prices, indicator values, or
signals.

### Step 6 --- User review

The trader can review, save, dismiss, or simulate a potential setup. The
MVP does not place live trades.

### Example trader profile

``` yaml
trader_profile:
  market:
    type: crypto
    provider: configured_provider
    symbols:
      - BTCUSDT
      - ETHUSDT

  trading:
    style: swing
    timeframe: 4h

  strategies:
    enabled:
      - ema_crossover
      - rsi_filter
      - macd_confirmation

  risk:
    risk_per_trade_percent: 1
    max_daily_loss_percent: 3
    max_open_positions: 3

  notifications:
    telegram: true
    dashboard: true

  execution:
    mode: paper_trading
```

This is an illustrative profile. Supported providers, symbols, and risk
settings depend on the implementation and data agreements.

------------------------------------------------------------------------

## 6. Modular Agent Architecture

The system should use a central orchestrator that coordinates
specialised modules. These modules can initially be deterministic
services and tool-driven workflows; they do not all need separate LLMs.

### 6.1 Orchestrator

-   Receives user requests.
-   Loads the user's workspace and configuration.
-   Determines which modules are required.
-   Coordinates module execution.
-   Applies permissions and workflow policies.
-   Produces a structured response.

### 6.2 Market Agent

-   Retrieves and validates market data.
-   Calculates indicators.
-   Summarises market conditions.

### 6.3 News Agent

-   Retrieves relevant news and event information.
-   Summarises sources and timestamps.
-   Provides contextual analysis.

### 6.4 Risk Agent

-   Runs deterministic risk calculations.
-   Enforces configured limits.
-   Rejects incomplete or invalid inputs.

### 6.5 Strategy Agent

-   Evaluates configured strategy rules.
-   Generates structured potential setups.
-   Explains which conditions passed or failed.

### 6.6 Backtest Agent

-   Runs historical simulations.
-   Reports assumptions and metrics.
-   Compares strategy versions.

### 6.7 Notification Agent

-   Formats and dispatches alerts.
-   Applies user preferences and rate limits.
-   Records delivery status.

### Architecture overview

``` text
                  TRADEPILOT ORCHESTRATOR
                            |
        +-------------------+-------------------+
        |         |         |         |         |
      Market     News      Risk    Strategy   Backtest
      Module    Module    Module    Module     Module
        |         |         |         |         |
        +-------------------+-------------------+
                            |
                Validated structured outputs
                            |
                 AI explanation / response
                            |
             Dashboard / Telegram / Email
                            |
                 Customer workspace
```

### Core design principle

**The LLM explains and coordinates; validated software calculates and
enforces.**

Never rely on an LLM alone to calculate market prices, technical
indicators, position sizes, stop losses, or risk limits.

------------------------------------------------------------------------

## 7. Customisation and Extensibility

The platform must support customer-specific configurations without
creating a separate codebase for every customer.

### Configurable dimensions

  Dimension       Examples
  --------------- ------------------------------------------------
  Market          Crypto, Forex, Indian stocks, US stocks
  Data provider   Provider-specific adapters
  Trading style   Scalping, intraday, swing, positional
  Timeframes      1m, 5m, 15m, 1h, 4h, 1d
  Indicators      EMA, RSI, MACD, ATR, VWAP
  Strategy type   Breakout, trend following, mean reversion
  Risk settings   User-defined limits within product constraints
  Notifications   Telegram, dashboard, email
  AI provider     Configurable model provider
  Custom logic    Structured user-defined strategy rules

### Strategy Builder

Users should be able to define rules in plain language or through a
visual interface.

Example:

> When EMA 20 crosses above EMA 50, RSI is above 50, and volume exceeds
> its recent average, identify a potential bullish setup.

The system should: 1. Convert the request into a structured strategy
definition. 2. Show the user the exact rules. 3. Validate indicators,
timeframes, and parameters. 4. Ask for confirmation. 5. Backtest the
strategy. 6. Allow paper-trading evaluation. 7. Version every change.

Do not execute arbitrary user-provided code or allow prompts to bypass
risk controls.

------------------------------------------------------------------------

## 8. User Interface

The product should have three primary interfaces.

### 8.1 Trading Dashboard

-   Market overview.
-   Watchlists.
-   Potential setups.
-   Market and indicator charts.
-   Risk overview.
-   Paper-trading history.
-   Performance analytics.
-   Recent alerts.

### 8.2 Conversational AI Assistant

Example user requests: - "Analyse BTC on the 4-hour timeframe." -
"Explain why this setup was generated." - "Check my watchlist for
configured strategy conditions." - "Compare my two paper-trading
strategies." - "Summarise my paper-trading performance this week."

Responses should include evidence, timestamps, source information, and
uncertainty where relevant.

### 8.3 Strategy and Configuration Studio

-   Create and edit strategies.
-   Configure indicators.
-   Set risk constraints.
-   Run backtests.
-   Manage data-provider connections.
-   Configure notifications.
-   View strategy versions and audit history.

### UX principles

-   Clear separation between data, calculations, and AI-generated
    explanations.
-   Display data timestamps and delayed-data warnings.
-   Never use visual design to imply certainty.
-   Make risk information prominent.
-   Provide transparent explanations for triggered and rejected setups.

------------------------------------------------------------------------

## 9. Technical Stack

A practical initial stack for a small development team:

  -----------------------------------------------------------------------
  Layer                   Recommended technology  Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                Next.js + TypeScript    Web application

  Backend                 Python + FastAPI        API and business logic

  Orchestration           LangGraph or a          Agent workflows
                          lightweight workflow    
                          layer                   

  AI models               OpenAI API and optional Explanations and
                          open-source adapters    language interface

  Market data             Exchange and            Price and volume data
                          market-data provider    
                          APIs                    

  Calculations            pandas, NumPy,          Indicators and
                          validated indicator     analytics
                          library                 

  Backtesting             vectorbt or Backtrader  Historical testing

  Database                PostgreSQL              Persistent application
                                                  data

  Cache and jobs          Redis + background      Caching and scheduled
                          worker                  jobs

  Notifications           Telegram Bot API        Alerts

  Deployment              Docker                  Reproducible services

  Monitoring              Structured logs and     Reliability
                          error monitoring        
  -----------------------------------------------------------------------

Technology choices should be confirmed during implementation based on
licensing, maintenance, compatibility, and provider terms.

------------------------------------------------------------------------

## 10. Suggested Repository Structure

``` text
tradepilot/
│
├── apps/
│   ├── api/
│   ├── dashboard/
│   └── telegram_bot/
│
├── core/
│   ├── orchestrator/
│   ├── agent_registry/
│   ├── configuration/
│   ├── permissions/
│   └── tenancy/
│
├── agents/
│   ├── market_agent/
│   ├── news_agent/
│   ├── risk_agent/
│   ├── strategy_agent/
│   ├── backtest_agent/
│   └── notification_agent/
│
├── integrations/
│   ├── exchanges/
│   ├── market_data/
│   ├── news/
│   ├── llm_providers/
│   └── notifications/
│
├── analytics/
│   ├── indicators/
│   ├── signals/
│   └── performance/
│
├── execution/
│   └── paper_trading/
│
├── database/
├── tests/
├── config/
├── docs/
├── scripts/
├── Dockerfile
└── docker-compose.yml
```

This is a proposed structure, not an existing implementation.

------------------------------------------------------------------------

## 11. Database Design

Use a multi-tenant data model. Each customer or workspace must have
explicit ownership and access boundaries.

  Table                Purpose
  -------------------- -----------------------------------
  users                User accounts
  workspaces           Customer workspaces
  workspace_members    Workspace access and roles
  trader_profiles      Trading preferences
  market_connections   Provider connection metadata
  strategies           Strategy definitions
  strategy_versions    Versioned strategy rules
  watchlists           Tracked assets
  market_snapshots     Cached or stored market data
  analysis_results     Agent analysis outputs
  trade_signals        Potential setups and status
  paper_trades         Simulated trades
  portfolios           Paper portfolio configurations
  risk_profiles        Risk constraints
  notifications        Alert history
  subscriptions        Customer plans
  audit_logs           Important user and system actions

### Data isolation requirements

-   Every tenant-owned record must include a workspace or tenant
    identifier.
-   Enforce authorisation at the API and database layers.
-   Use PostgreSQL row-level security where appropriate.
-   Test cross-tenant access explicitly.
-   Never trust a workspace ID supplied by a client without checking
    membership.
-   Keep credentials out of ordinary application records and model
    prompts.

------------------------------------------------------------------------

## 12. API Design

Initial API groups:

``` text
/auth
  POST /register
  POST /login
  POST /logout

/workspaces
  GET  /
  POST /
  GET  /{workspace_id}

/profiles
  GET  /me
  PUT  /me

/market
  GET  /symbols
  GET  /candles
  GET  /overview

/strategies
  GET  /
  POST /
  GET  /{strategy_id}
  PUT  /{strategy_id}
  POST /{strategy_id}/validate
  POST /{strategy_id}/backtest

/analysis
  POST /run
  GET  /history
  GET  /{analysis_id}

/risk
  POST /calculate-position-size
  POST /validate-trade

/paper-trading
  GET  /portfolio
  POST /trades
  GET  /trades
  POST /trades/{trade_id}/close

/notifications
  GET  /
  PUT  /preferences
```

All endpoints need authentication, workspace authorisation, input
validation, rate limits, and audit logging where appropriate. These are
illustrative contracts; detailed schemas should be designed before
implementation.

------------------------------------------------------------------------

## 13. Market Data and Integration Strategy

Use adapter interfaces so that the core application is not tied to one
exchange or provider.

### Adapter responsibilities

-   Authentication and connection management.
-   Symbol mapping.
-   Historical candle retrieval.
-   Latest market data retrieval.
-   Rate-limit handling.
-   Timestamp normalisation.
-   Error handling.
-   Data-quality validation.

### Data quality checks

-   Missing candles.
-   Duplicate records.
-   Invalid OHLC relationships.
-   Stale timestamps.
-   Unexpected price jumps.
-   Provider outages.
-   Timezone and interval consistency.

Do not advertise real-time data unless the chosen provider, licence,
infrastructure, and implementation actually support it.

------------------------------------------------------------------------

## 14. Security, Reliability, and Responsible Product Design

Financial products need strong controls from the beginning.

### Security

-   Encrypt sensitive credentials at rest.
-   Use a managed secrets system where possible.
-   Never expose exchange credentials to the LLM.
-   Request read-only API permissions for initial integrations.
-   Never request withdrawal permissions.
-   Use least-privilege service accounts.
-   Apply rate limiting and abuse protection.
-   Maintain security and access audit logs.
-   Protect webhook endpoints with authentication and replay protection.

### Reliability

-   Validate market data before calculations.
-   Display source and timestamp.
-   Handle provider outages gracefully.
-   Do not generate a signal from incomplete or stale data.
-   Use idempotent background jobs.
-   Monitor latency, failures, and alert delivery.
-   Test strategy calculations against known datasets.

### AI safeguards

-   LLMs must not invent prices or indicator values.
-   LLMs must not override deterministic risk controls.
-   Tool outputs should be schema-validated.
-   User prompts must not bypass permissions.
-   Explain uncertainty and limitations.
-   Preserve evidence and source references for analysis.

### Product boundaries

The MVP is a research, analytics, alerting, and paper-trading product.
It should not hold customer funds, manage withdrawals, or place live
trades.

Any future live-execution functionality requires a separate legal,
regulatory, broker/exchange, security, and operational assessment.
Requirements vary by jurisdiction and product activity. Obtain qualified
advice before offering execution or regulated services.

------------------------------------------------------------------------

## 15. MVP Scope

The first version should prove that traders repeatedly use the analysis,
strategy, and risk-management features.

### Include in MVP

-   Account creation and authentication.
-   Multi-tenant workspaces.
-   Trader profile and configuration.
-   One market-data integration.
-   Watchlists.
-   Candlestick data.
-   Core indicators: EMA, RSI, MACD, ATR.
-   One or two configurable strategy templates.
-   Deterministic risk calculator.
-   AI explanations based on structured outputs.
-   Telegram alerts.
-   Basic web dashboard.
-   Paper-trading ledger.
-   Basic analysis history.
-   Audit logs and tenant-isolation tests.

### Exclude from MVP

-   Autonomous live trading.
-   Copy trading.
-   Social trading network.
-   Mobile applications.
-   Many simultaneous exchange integrations.
-   Custom model training.
-   Complex multi-agent LLM infrastructure.
-   Guaranteed-profit or prediction claims.

### Initial market recommendation

Design adapters for multiple markets, but launch with one market and one
or two trading styles. Choose the first integration based on access to
reliable data, tester demand, licensing, and the developer's ability to
validate it.

------------------------------------------------------------------------

## 16. Six-Week Development Roadmap

This is a target plan for a focused MVP. Adjust it based on available
time and integration complexity.

### Week 1 --- Foundation

-   Create repository and development environment.
-   Set up FastAPI and Next.js.
-   Implement authentication.
-   Create workspaces and tenant boundaries.
-   Build configuration model.
-   Define market-data adapter interface.

### Week 2 --- Market Intelligence

-   Integrate first market-data provider.
-   Retrieve and validate candle data.
-   Implement EMA, RSI, MACD, and ATR.
-   Create watchlists.
-   Build first market-analysis service.

### Week 3 --- Strategy Engine

-   Define structured strategy schema.
-   Implement strategy templates.
-   Build rule evaluation.
-   Add input validation.
-   Record triggered and rejected conditions.

### Week 4 --- AI and Risk

-   Add orchestrator workflows.
-   Connect LLM for explanations.
-   Implement deterministic position sizing and risk checks.
-   Add Telegram notifications.
-   Add audit records.

### Week 5 --- Dashboard and Paper Trading

-   Build dashboard views.
-   Add analysis history.
-   Add strategy configuration UI.
-   Implement paper-trading ledger.
-   Add basic performance reporting.

### Week 6 --- Testing and Private Beta

-   Test calculations against reference datasets.
-   Test stale and missing data handling.
-   Test tenant isolation.
-   Test API permissions and rate limits.
-   Deploy to a controlled environment.
-   Onboard 5--10 testers.
-   Collect structured feedback.

------------------------------------------------------------------------

## 17. Private Beta Strategy

Start with 5--10 friends who actively trade. Do not give everyone the
same configuration.

Recruit a mix of: - Crypto swing trader. - Crypto intraday trader. -
Equity swing trader. - Forex trader, if a suitable data provider is
available. - Trader with a custom indicator strategy.

### Tester onboarding

1.  Interview the trader about their existing workflow.
2.  Record their preferred assets, timeframes, and strategies.
3.  Configure their workspace.
4.  Explain the product's limitations.
5.  Start with analysis and paper trading.
6.  Observe usage and collect feedback.
7.  Review alert relevance and calculation accuracy.
8.  Ask whether they would pay and why.

### Feedback questions

-   Was the data correct and current?
-   Did the explanation match the underlying calculations?
-   Were alerts useful or noisy?
-   Did the product save time?
-   Was configuration understandable?
-   What would make the user return?
-   Would the user pay for it? At what price and for which feature?

Do not use profitable simulated trades as proof of future performance.

------------------------------------------------------------------------

## 18. Go-to-Market Strategy

### Stage 1 --- Private beta

Use personal networks to recruit active traders and validate the
product.

### Stage 2 --- Individual subscriptions

Offer paid plans to users who repeatedly use the product and understand
its value.

### Stage 3 --- Community partnerships

Approach trading educators, Telegram and Discord community owners, and
independent trading groups. Offer demonstrations and a dedicated branded
workspace.

### Stage 4 --- White-label licensing

Provide: - Custom branding. - Dedicated workspace. - Configurable
strategies. - Admin controls. - Customer management. - Usage
reporting. - Optional private deployment.

### Stage 5 --- Enterprise

Explore API access, private deployments, and integrations for
businesses, subject to commercial and regulatory review.

### Initial customer acquisition targets

These are internal targets, not guaranteed outcomes: - Interview 20
traders. - Recruit 5--10 beta users. - Demonstrate the product to 10
relevant prospects. - Identify 5 potential community or educator
partners. - Convert the first 3--5 paying customers.

------------------------------------------------------------------------

## 19. Business Model and Pricing Hypotheses

Pricing must be tested with real users. The following are starting
hypotheses, not validated market rates.

  ------------------------------------------------------------------------
  Offering                  Initial price hypothesis Potential features
  --------------------- ---------------------------- ---------------------
  Starter                                       Free Limited watchlists
                                                     and analysis

  Pro                                     ₹999/month Personal
                                                     configuration,
                                                     alerts, analysis
                                                     history

  Advanced                              ₹2,499/month More strategies,
                                                     backtesting, advanced
                                                     reporting

  White-label setup                 ₹25,000--₹75,000 Branding and
                                                     workspace
                                                     configuration

  Enterprise                                  Custom Private deployment,
                                                     API access, support
  ------------------------------------------------------------------------

### Revenue example

At ₹999 per month:

    Paying customers   Gross monthly subscription revenue
  ------------------ ------------------------------------
                  25                              ₹24,975
                  50                              ₹49,950
                 100                              ₹99,900
                 250                            ₹2,49,750
                 500                            ₹4,99,500

These figures are before infrastructure, data licensing, AI usage,
payment fees, taxes, support, refunds, and churn. They are not profit
forecasts.

### Cost areas

-   AI model usage.
-   Market-data subscriptions and licences.
-   Hosting and database.
-   Monitoring and backups.
-   Messaging and email.
-   Payment processing.
-   Customer support.
-   Legal and compliance advice.

Use usage limits and cost monitoring from the start. Do not assume that
market data or redistribution rights are free.

------------------------------------------------------------------------

## 20. Success Metrics

Measure product utility and reliability rather than feature count or
claimed trading returns.

Suggested initial validation targets:

  Metric                               Initial target
  ---------------------------------- ----------------
  Private beta users                               10
  Users configuring a strategy                      8
  Weekly active users                               7
  Users returning after four weeks                  5
  Paying customers                               3--5
  Critical data errors                              0
  Cross-tenant data leaks                           0

Additional metrics: - Analysis completion rate. - Market-data
freshness. - Alert delivery success. - Strategy validation failures. -
Paper-trade record consistency. - User-reported usefulness. - Support
requests per user. - Cost per active user. - Subscription conversion and
churn.

------------------------------------------------------------------------

## 21. Main Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Incorrect or stale market data      Validation, timestamps, provider
                                      monitoring

  Misleading AI explanations          Ground LLM responses in structured
                                      calculations

  Overfitting strategies              Out-of-sample testing and realistic
                                      assumptions

  False confidence in backtests       Disclose fees, slippage,
                                      assumptions, and limitations

  Customer data leakage               Tenant isolation and security
                                      testing

  High AI costs                       Usage quotas, caching, smaller
                                      models where appropriate

  Provider outages                    Adapter abstraction and graceful
                                      failure

  Regulatory exposure                 Keep MVP read-only and obtain
                                      qualified legal advice

  Weak customer retention             Interview users and prioritise
                                      recurring workflows

  Unsupported performance claims      No guarantees; substantiate any
                                      published claims
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 22. Product Principles

1.  **One core platform, many customer configurations.**
2.  **No separate codebase per customer.**
3.  **Deterministic calculations for indicators, position sizing, and
    risk.**
4.  **LLMs explain validated data; they do not invent it.**
5.  **Every analysis should show its source and timestamp.**
6.  **No signal should be generated from invalid or stale data.**
7.  **Customer data must be isolated.**
8.  **Strategies must be testable and versioned.**
9.  **Paper trading before any live-execution consideration.**
10. **Never promise guaranteed returns.**

------------------------------------------------------------------------

## 23. Immediate Next Steps

Before implementation, make these decisions:

### Product decisions

-   Select the first market integration.
-   Select the first data provider.
-   Choose web, Telegram, or both for the initial user experience.
-   Decide whether the first release is a prototype or
    production-oriented MVP.
-   Confirm the initial deployment approach.

### Engineering decisions

-   Define the workspace and tenant model.
-   Define the trader configuration schema.
-   Define the strategy schema.
-   Define market-data adapter contracts.
-   Define calculation and validation tests.
-   Define API contracts.
-   Define security and audit requirements.

### Customer validation decisions

-   Identify the first 5--10 testers.
-   Interview them before building too many features.
-   Agree on what a useful analysis looks like.
-   Run paper-trading pilots.
-   Ask for willingness-to-pay feedback.

------------------------------------------------------------------------

## 24. Final Product Direction

TradePilot AI should become a configurable AI trading intelligence
platform, not merely a bot that sends buy and sell messages.

Its long-term advantage should come from: - A reliable modular
architecture. - Flexible customer configurations. - Transparent and
testable strategy evaluation. - Strong risk and data-quality controls. -
Useful trader workflows. - White-label deployment capabilities. - Trust
earned through reliability rather than exaggerated performance claims.

**Build the platform once. Configure it for each trader. Validate it
with real users. Sell only what consistently delivers value.**
