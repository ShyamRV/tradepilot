"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthScreens } from "@/components/AuthScreens";
import { AppShell } from "@/components/AppShell";
import { useTheme } from "@/components/ThemeProvider";
import { useWorkspace } from "@/components/WorkspaceProvider";

const LEGAL_PATHS = new Set(["/privacy", "/terms", "/support"]);

export function AppGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { gate, data } = useWorkspace();
  const isLegal = LEGAL_PATHS.has(pathname);

  if (isLegal && gate !== "ready") {
    return <LegalFrame>{children}</LegalFrame>;
  }

  if (gate !== "ready") return <AuthScreens />;
  if (!data) {
    return (
      <main className="centerState" role="status">
        <div className="orbit" aria-hidden="true" />
        Preparing workspace…
      </main>
    );
  }

  return <AppShell>{children}</AppShell>;
}

function LegalFrame({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();

  return (
    <main className="legalFrame">
      <header className="legalFrameHeader">
        <Link href="/" className="authBrand">
          TradePilot <em>AI</em>
        </Link>
        <div className="topActions">
          <div className="honestyBanner compact" role="note">
            <span>Paper trading only</span>
            <span aria-hidden="true">·</span>
            <span>Not investment advice</span>
            <span aria-hidden="true">·</span>
            <span>Delayed/EOD data</span>
          </div>
          <button type="button" className="ghostButton" onClick={toggleTheme}>
            {theme === "dark" ? "Light" : "Dark"}
          </button>
          <Link className="ghostButton" href="/">
            Sign in
          </Link>
        </div>
      </header>
      <nav className="legalNav inline" aria-label="Legal">
        <Link href="/privacy" aria-current={pathname === "/privacy" ? "page" : undefined}>
          Privacy
        </Link>
        <Link href="/terms" aria-current={pathname === "/terms" ? "page" : undefined}>
          Terms
        </Link>
        <Link href="/support" aria-current={pathname === "/support" ? "page" : undefined}>
          Support
        </Link>
      </nav>
      <div className="pageBody legalFrameBody">{children}</div>
    </main>
  );
}
