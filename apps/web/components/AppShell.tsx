"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/components/ThemeProvider";
import { useWorkspace } from "@/components/WorkspaceProvider";

const NAV = [
  { href: "/overview", label: "Overview", icon: "◈" },
  { href: "/markets", label: "Markets", icon: "◔" },
  { href: "/terminal/NSE/RELIANCE", label: "Terminal", icon: "⌁" },
  { href: "/watchlist", label: "Watchlist", icon: "▦" },
  { href: "/agents", label: "AI Agents", icon: "✦" },
  { href: "/strategies", label: "Strategies", icon: "⊹" },
  { href: "/analysis", label: "Analysis", icon: "◎" },
  { href: "/portfolio", label: "Portfolio", icon: "▣" },
  { href: "/backtests", label: "Backtests", icon: "↗" }
];

const LEGAL = [
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/support", label: "Support" }
];

const PAGE_TITLES: Record<string, string> = {
  "/privacy": "Privacy Policy",
  "/terms": "Terms of Use",
  "/support": "Support"
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const { data, apiConfigured, handleLogout, busy, error, reload } = useWorkspace();
  const legalTitle = PAGE_TITLES[pathname];

  return (
    <div className="appShell">
      <aside className="sidebar" aria-label="Primary">
        <Link href="/overview" className="brand">
          <span className="brandMark" aria-hidden="true" />
          <span>
            TradePilot <em>AI</em>
          </span>
        </Link>

        <nav>
          {NAV.map((item) => {
            const current =
              pathname === item.href ||
              (item.href.startsWith("/terminal") && pathname.startsWith("/terminal")) ||
              (item.href === "/agents" && pathname.startsWith("/agents")) ||
              (item.href === "/markets" && pathname.startsWith("/markets"));
            return (
              <Link key={item.href} href={item.href} aria-current={current ? "page" : undefined}>
                <span className="navIcon" aria-hidden="true">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sideFooter">
          <button type="button" className="themeToggle" onClick={toggleTheme} aria-label="Toggle color theme">
            <span className="themeKnob" data-mode={theme} />
            <span>{theme === "dark" ? "Dark mode" : "Light mode"}</span>
          </button>
          <div className="sideNote">
            <strong>Paper mode</strong>
            <span>No live orders. Delayed / EOD research only. Not investment advice.</span>
          </div>
          <nav className="legalNav" aria-label="Legal">
            {LEGAL.map((item) => (
              <Link key={item.href} href={item.href} aria-current={pathname === item.href ? "page" : undefined}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </aside>

      <div className="workspaceFrame">
        <header className="topbar">
          <div>
            <p className="eyebrow">{legalTitle ? "Legal" : "Workspace"}</p>
            <h1>{legalTitle ?? data?.workspace.name ?? "TradePilot"}</h1>
            <p className="topMeta">
              {data?.workspace.market ?? "NSE cash equities"} · {data?.workspace.mode ?? "Paper trading"}
            </p>
          </div>
          <div className="topActions">
            <span className="pill warn">{data?.freshness.status?.toUpperCase() ?? "EOD"}</span>
            <button type="button" className="ghostButton" onClick={toggleTheme}>
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            {apiConfigured ? (
              <button type="button" className="ghostButton" onClick={handleLogout}>
                Log out
              </button>
            ) : (
              <span className="avatar" aria-label="Demo account">
                DE
              </span>
            )}
          </div>
        </header>

        <div className="honestyBanner" role="note">
          <span>Paper trading only</span>
          <span aria-hidden="true">·</span>
          <span>Not investment advice</span>
          <span aria-hidden="true">·</span>
          <span>Delayed/EOD data</span>
        </div>

        {data && (
          <div className="freshness" role="status">
            <div>
              <strong>{data.freshness.delay}</strong>
              <span>Market data as of {data.freshness.asOf}. Confirm current prices before acting.</span>
            </div>
            <span className="pill warn">AS-OF</span>
          </div>
        )}

        {busy && (
          <div className="message" role="status">
            Syncing workspace…
          </div>
        )}
        {error && (
          <div className="message error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={reload}>
              Retry
            </button>
          </div>
        )}
        {!apiConfigured && (
          <p className="demoLabel" role="status">
            Demo mode · Illustrative sample data only · NEXT_PUBLIC_API_URL unset · Not live market data · Not investment
            advice
          </p>
        )}

        <div className="pageBody">{children}</div>
      </div>
    </div>
  );
}
