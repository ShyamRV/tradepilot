"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { BrandLogo } from "@/components/BrandLogo";
import { useTheme } from "@/components/ThemeProvider";
import { useWorkspace } from "@/components/WorkspaceProvider";

const NAV = [
  { href: "/overview", label: "Overview", icon: "◈" },
  { href: "/playground", label: "Playground", icon: "▹" },
  { href: "/markets", label: "Markets", icon: "◔" },
  { href: "/terminal/NSE/RELIANCE", label: "Terminal", icon: "⌁" },
  { href: "/watchlist", label: "Watchlist", icon: "▦" },
  { href: "/agents", label: "AI Agents", icon: "✦" },
  { href: "/strategies", label: "Strategies", icon: "⊹" },
  { href: "/analysis", label: "Analysis", icon: "◎" },
  { href: "/portfolio", label: "Portfolio", icon: "▣" },
  { href: "/backtests", label: "Backtests", icon: "↗" },
  { href: "/account", label: "Account", icon: "◉" }
];

const LEGAL = [
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/support", label: "Support" }
];

const PAGE_TITLES: Record<string, string> = {
  "/privacy": "Privacy Policy",
  "/terms": "Terms of Use",
  "/support": "Support",
  "/account": "Account"
};

const SIDEBAR_KEY = "athena.sidebarCollapsed";
const LEGACY_SIDEBAR_KEY = "tradepilot.sidebarCollapsed";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const { data, apiConfigured, handleLogout, busy, error, reload, profile } = useWorkspace();
  const legalTitle = PAGE_TITLES[pathname];
  const [collapsed, setCollapsed] = useState(true);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(SIDEBAR_KEY) ?? window.localStorage.getItem(LEGACY_SIDEBAR_KEY);
      if (saved === "0" || saved === "1") {
        setCollapsed(saved === "1");
        return;
      }
      setCollapsed(window.matchMedia("(max-width: 900px)").matches);
    } catch {
      // Ignore storage failures.
    }
  }, []);

  function toggleSidebar() {
    setCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0");
      } catch {
        // Ignore storage failures.
      }
      return next;
    });
  }

  const initials = (profile?.name || profile?.email || "AT")
    .split(/[\s@]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("") || "AT";

  return (
    <div className={`appShell ${collapsed ? "sidebarCollapsed" : ""}`}>
      <aside className="sidebar" aria-label="Primary">
        <div className="sidebarTop">
          <BrandLogo compact showWordmark={!collapsed} />
          <button
            type="button"
            className="sidebarToggle"
            onClick={toggleSidebar}
            aria-label={collapsed ? "Open sidebar" : "Close sidebar"}
            aria-expanded={!collapsed}
            title={collapsed ? "Open sidebar" : "Close sidebar"}
          >
            {collapsed ? "»" : "«"}
          </button>
        </div>

        <nav>
          {NAV.map((item) => {
            const current =
              pathname === item.href ||
              (item.href.startsWith("/terminal") && pathname.startsWith("/terminal")) ||
              (item.href === "/agents" && pathname.startsWith("/agents")) ||
              (item.href === "/playground" && pathname.startsWith("/playground")) ||
              (item.href === "/markets" && pathname.startsWith("/markets")) ||
              (item.href === "/account" && pathname.startsWith("/account"));
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={current ? "page" : undefined}
                title={item.label}
                onClick={() => {
                  if (typeof window !== "undefined" && window.matchMedia("(max-width: 900px)").matches) {
                    setCollapsed(true);
                    try {
                      window.localStorage.setItem(SIDEBAR_KEY, "1");
                    } catch {
                      // Ignore storage failures.
                    }
                  }
                }}
              >
                <span className="navIcon" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="navLabel">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sideFooter">
          <button type="button" className="themeToggle" onClick={toggleTheme} aria-label="Toggle color theme">
            <span className="themeKnob" data-mode={theme} />
            <span className="navLabel">{theme === "dark" ? "Dark mode" : "Light mode"}</span>
          </button>
          <div className="sideNote">
            <strong>Paper mode</strong>
            <span className="navLabel">No live orders. Not investment advice.</span>
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
          <div className="topbarLead">
            <button
              type="button"
              className="sidebarToggle mobileSidebarToggle"
              onClick={toggleSidebar}
              aria-label={collapsed ? "Open sidebar" : "Close sidebar"}
            >
              ☰
            </button>
            <div>
              <p className="eyebrow">{legalTitle ? "Legal" : "Workspace"}</p>
              <h1>{legalTitle ?? data?.workspace.name ?? "Athena"}</h1>
              <p className="topMeta">
                {data?.workspace.market ?? "NSE cash equities"} · {data?.workspace.mode ?? "Paper trading"}
              </p>
            </div>
          </div>
          <div className="topActions">
            <span className="pill">Paper</span>
            <button type="button" className="ghostButton" onClick={toggleTheme}>
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <Link href="/account" className="avatarLink" aria-label="Open account">
              <span className="avatar">{apiConfigured ? initials : "DE"}</span>
            </Link>
            {apiConfigured && (
              <button type="button" className="ghostButton" onClick={handleLogout}>
                Log out
              </button>
            )}
          </div>
        </header>

        <div className="honestyBanner" role="note">
          <span>Paper trading only</span>
          <span aria-hidden="true">·</span>
          <span>Not investment advice</span>
        </div>

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

        <div className="pageBody">{children}</div>
      </div>
    </div>
  );
}
