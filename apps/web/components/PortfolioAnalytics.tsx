"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { portfolioSeries } from "@/lib/trading";

export function PortfolioAnalytics() {
  const data = portfolioSeries();
  return (
    <section className="panel analyticsPanel">
      <header className="panelHeader"><div><p className="vizEyebrow">30-day paper account</p><h2>Portfolio vs benchmark</h2></div><span className="pill">INR</span></header>
      <div className="analyticsChart">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#33e1ff" stopOpacity={0.3}/><stop offset="100%" stopColor="#33e1ff" stopOpacity={0}/></linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,.1)" vertical={false} />
            <XAxis dataKey="day" hide />
            <YAxis domain={["dataMin - 10000", "dataMax + 10000"]} hide />
            <Tooltip formatter={(value) => `₹${Number(value).toLocaleString("en-IN")}`} contentStyle={{ background: "#11151d", border: "1px solid rgba(148,163,184,.2)", borderRadius: 12 }} />
            <Area type="monotone" dataKey="equity" stroke="#33e1ff" fill="url(#equityFill)" strokeWidth={2} />
            <Area type="monotone" dataKey="benchmark" stroke="#ffb020" fill="transparent" strokeWidth={1.5} strokeDasharray="4 4" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <footer className="chartLegend"><span><i className="cyanDot" />Paper equity</span><span><i className="amberDot" />Illustrative benchmark</span></footer>
    </section>
  );
}
