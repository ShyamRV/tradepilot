"use client";

import Link from "next/link";
import { use, useMemo, useState } from "react";
import { TradingChart } from "@/components/TradingChart";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { submitSandboxOrder } from "@/lib/trading-api";
import { instruments, orderSchema, type OrderInput } from "@/lib/trading";
import { useMarketStream } from "@/lib/use-market-stream";
import { useTradingStore } from "@/lib/trading-store";

type Props = { params: Promise<{ exchange: string; symbol: string }> };

export default function TerminalPage({ params }: Props) {
  const { apiConfigured, token, workspaceId, data } = useWorkspace();
  const route = use(params);
  const exchange = route.exchange.toUpperCase();
  const symbol = route.symbol.toUpperCase();
  const instrument = instruments.find((item) => item.exchange === exchange && item.symbol === symbol) ?? instruments[0];
  const { tick, status } = useMarketStream(instrument.exchange, instrument.symbol, instrument.price);
  const { watchlist, orders, toggleWatch, placeOrder, cancelOrder } = useTradingStore();
  const [query, setQuery] = useState("");
  const [side, setSide] = useState<OrderInput["side"]>("BUY");
  const [type, setType] = useState<OrderInput["type"]>("MARKET");
  const [quantity, setQuantity] = useState("1");
  const [limitPrice, setLimitPrice] = useState(instrument.price.toFixed(2));
  const [preview, setPreview] = useState<OrderInput | null>(null);
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"orders" | "positions" | "trades">("orders");
  const [submitting, setSubmitting] = useState(false);

  const results = useMemo(
    () =>
      query.length < 1
        ? []
        : instruments.filter((item) => `${item.symbol} ${item.name}`.toLowerCase().includes(query.toLowerCase())),
    [query]
  );
  const visibleWatchlist = instruments.filter((item) => watchlist.includes(item.symbol));
  const currentOrders = orders.filter((order) => order.symbol === instrument.symbol);
  const estimate = Number(quantity || 0) * (type === "LIMIT" ? Number(limitPrice || 0) : tick.price);

  function validate() {
    const parsed = orderSchema.safeParse({
      side,
      type,
      quantity,
      product: "CNC",
      limitPrice: type === "LIMIT" ? limitPrice : undefined
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Check order details.");
      return null;
    }
    setError("");
    return parsed.data;
  }

  async function submit() {
    if (!preview) return;
    setSubmitting(true);
    setError("");
    const idempotencyKey = crypto.randomUUID();
    try {
      let status: "OPEN" | "FILLED" | "REJECTED" | undefined;
      let reason = "";
      if (apiConfigured && token && workspaceId) {
        const result = await submitSandboxOrder(
          { token, workspaceId },
          {
            idempotency_key: idempotencyKey,
            symbol: instrument.symbol,
            side: preview.side.toLowerCase() as "buy" | "sell",
            quantity: preview.quantity,
            order_type: preview.type.toLowerCase() as "market" | "limit",
            limit_price: preview.limitPrice?.toString(),
            equity: String(data?.portfolio.equity ?? 1_000_000),
            cash: String(data?.portfolio.cash ?? 1_000_000)
          }
        );
        status =
          result.status === "filled"
            ? "FILLED"
            : ["accepted", "partially_filled"].includes(result.status)
              ? "OPEN"
              : "REJECTED";
        reason = result.reason ?? "";
      }
      const order = placeOrder(
        {
          ...preview,
          exchange: instrument.exchange,
          symbol: instrument.symbol,
          price: preview.type === "LIMIT" ? preview.limitPrice! : tick.price
        },
        status
      );
      setPreview(null);
      setFeedback(
        order.status === "REJECTED"
          ? `Sandbox order rejected${reason ? `: ${reason.replaceAll("_", " ")}` : "."}`
          : `${order.status === "FILLED" ? "Filled" : "Placed"} sandbox order ${order.id.slice(0, 8)}.`
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to submit sandbox order.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="terminalPage">
      <section className="instrumentBar" aria-label="Instrument controls">
        <div className="instrumentSearch">
          <label htmlFor="instrument-search">Search instruments</label>
          <input
            id="instrument-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Symbol or company"
            autoComplete="off"
          />
          {results.length > 0 && (
            <div className="searchResults">
              {results.map((item) => (
                <Link key={`${item.exchange}-${item.symbol}`} href={`/terminal/${item.exchange}/${item.symbol}`}>
                  <strong>{item.symbol}</strong><span>{item.exchange} · {item.name}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
        <div className="instrumentIdentity">
          <div><span className="exchangeTag">{instrument.exchange}</span><h2>{instrument.symbol}</h2></div>
          <span>{instrument.name}</span>
        </div>
        <div className="livePrice">
          <strong>₹{tick.price.toFixed(2)}</strong>
          <span className={tick.change >= 0 ? "positive" : "negative"}>{tick.change >= 0 ? "+" : ""}{tick.change.toFixed(2)}%</span>
        </div>
        <span className={`streamState ${status}`}><i />{status === "demo" ? "Simulated live" : status}</span>
        <button className="ghostButton" onClick={() => toggleWatch(instrument.symbol)}>
          {watchlist.includes(instrument.symbol) ? "★ Watching" : "☆ Watch"}
        </button>
      </section>

      <div className="terminalGrid">
        <aside className="watchRail panel" aria-label="Watchlist">
          <header className="panelHeader"><h2>Watchlist</h2><span>{visibleWatchlist.length}</span></header>
          {visibleWatchlist.map((item) => (
            <Link
              href={`/terminal/${item.exchange}/${item.symbol}`}
              key={`${item.exchange}-${item.symbol}`}
              aria-current={item.symbol === instrument.symbol ? "page" : undefined}
            >
              <span><strong>{item.symbol}</strong><small>{item.exchange}</small></span>
              <span className={item.change >= 0 ? "positive" : "negative"}>
                ₹{item.price.toFixed(2)}<small>{item.change >= 0 ? "+" : ""}{item.change}%</small>
              </span>
            </Link>
          ))}
        </aside>

        <main className="terminalMain stack">
          <section className="panel chartPanel">
            <header className="chartToolbar">
              <div><strong>5m</strong><button type="button">15m</button><button type="button">1h</button><button type="button">1D</button></div>
              <span>O {instrument.price.toFixed(2)} · H {(instrument.price * 1.007).toFixed(2)} · L {(instrument.price * .993).toFixed(2)}</span>
            </header>
            <TradingChart price={instrument.price} />
            <p className="chartCaption">Illustrative candles and volume. Streamed last price may differ from chart history.</p>
          </section>

          <section className="panel blotter">
            <div className="tabList" role="tablist">
              {(["orders", "positions", "trades"] as const).map((item) => (
                <button key={item} role="tab" aria-selected={tab === item} onClick={() => setTab(item)}>{item}</button>
              ))}
            </div>
            {tab === "orders" && (
              <DataTable
                headers={["Time", "Side", "Type", "Qty", "Price", "Status", ""]}
                empty="No paper orders for this instrument."
                rows={currentOrders.map((order) => [
                  new Date(order.placedAt).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
                  order.side,
                  order.type,
                  order.quantity,
                  `₹${order.price.toFixed(2)}`,
                  order.status,
                  order.status === "OPEN" ? <button className="textButton" onClick={() => cancelOrder(order.id)}>Cancel</button> : "—"
                ])}
              />
            )}
            {tab === "positions" && <DataTable headers={["Symbol", "Qty", "Average", "LTP", "P&L"]} rows={[[instrument.symbol, 18, "₹1,476.20", `₹${tick.price.toFixed(2)}`, <span key="position-pnl" className="positive">+₹1,207.80</span>]]} />}
            {tab === "trades" && <DataTable headers={["Time", "Side", "Qty", "Price", "Product"]} rows={currentOrders.filter((order) => order.status === "FILLED").map((order) => ["Today", order.side, order.quantity, `₹${order.price.toFixed(2)}`, order.product])} empty="No completed trades." />}
          </section>
        </main>

        <aside className="terminalSide stack">
          <section className="panel orderTicket">
            <header className="panelHeader"><h2>Paper order</h2><span className="pill warn">SIMULATED</span></header>
            <div className="sideSwitch">
              <button className={side === "BUY" ? "active buy" : ""} onClick={() => setSide("BUY")}>Buy</button>
              <button className={side === "SELL" ? "active sell" : ""} onClick={() => setSide("SELL")}>Sell</button>
            </div>
            <label>Order type<select value={type} onChange={(event) => setType(event.target.value as OrderInput["type"])}><option>MARKET</option><option>LIMIT</option></select></label>
            <label>Quantity<input inputMode="numeric" value={quantity} onChange={(event) => setQuantity(event.target.value)} /></label>
            {type === "LIMIT" && <label>Limit price<input inputMode="decimal" value={limitPrice} onChange={(event) => setLimitPrice(event.target.value)} /></label>}
            <div className="estimate"><span>Estimated value</span><strong>₹{estimate.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</strong></div>
            {error && <p className="fieldError" role="alert">{error}</p>}
            {feedback && <p className="successMessage" role="status">{feedback}</p>}
            <button type="button" className="primary" data-testid="preview-order" onClick={() => { const valid = validate(); if (valid) setPreview(valid); }}>Preview {side.toLowerCase()}</button>
          </section>
          <Depth price={tick.price} />
        </aside>
      </div>

      {preview && (
        <div className="modalBackdrop" role="presentation">
          <section className="confirmModal" role="dialog" aria-modal="true" aria-labelledby="preview-title">
            <h2 id="preview-title">Review paper order</h2>
            <p>{preview.side} {preview.quantity} {instrument.symbol} at {preview.type === "MARKET" ? "market" : `₹${preview.limitPrice}`}</p>
            <dl><div><dt>Product</dt><dd>{preview.product}</dd></div><div><dt>Estimated value</dt><dd>₹{estimate.toLocaleString("en-IN")}</dd></div></dl>
            <div className="riskNotice">Paper trading only. Prices, fills, slippage, fees and taxes are simulated. This is not investment advice.</div>
            <div className="modalActions"><button className="ghostButton" onClick={() => setPreview(null)}>Back</button><button className="primary" disabled={submitting} onClick={() => void submit()}>{submitting ? "Submitting…" : "Submit sandbox order"}</button></div>
          </section>
        </div>
      )}
    </div>
  );
}

function Depth({ price }: { price: number }) {
  return (
    <section className="panel depth">
      <header className="panelHeader"><h2>Market depth</h2><span className="pill">Demo</span></header>
      <div className="depthHead"><span>Bid qty</span><span>Price</span><span>Ask qty</span></div>
      {Array.from({ length: 5 }, (_, index) => (
        <div className="depthRow" key={index}>
          <span className="positive">{120 + index * 87}</span><span>₹{(price - (5 - index) * .05).toFixed(2)}</span><span className="negative">{190 + index * 63}</span>
        </div>
      ))}
    </section>
  );
}

function DataTable({ headers, rows, empty = "No data." }: { headers: string[]; rows: React.ReactNode[][]; empty?: string }) {
  if (!rows.length) return <div className="emptyState">{empty}</div>;
  return <div className="tableWrap"><table><thead><tr>{headers.map((item) => <th key={item}>{item}</th>)}</tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, index) => <td key={index}>{cell}</td>)}</tr>)}</tbody></table></div>;
}
