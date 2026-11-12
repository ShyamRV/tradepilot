"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthMode } from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";
import { useWorkspace } from "@/components/WorkspaceProvider";

export function AuthScreens() {
  const { gate, busy, error, workspaces, handleAuth, handleCreate, handleSelect, handleLogout, retryWorkspaces } =
    useWorkspace();
  const { theme, toggleTheme } = useTheme();

  if (gate === "boot") {
    return (
      <main className="centerState" role="status">
        <div className="orbit" aria-hidden="true" />
        Restoring your session…
      </main>
    );
  }

  if (gate === "auth") {
    return <AuthPanel busy={busy} error={error} theme={theme} onToggleTheme={toggleTheme} onSubmit={handleAuth} />;
  }

  return (
    <WorkspacePanel
      items={workspaces}
      busy={busy}
      error={error}
      theme={theme}
      onToggleTheme={toggleTheme}
      onSelect={handleSelect}
      onCreate={handleCreate}
      onLogout={handleLogout}
      onRetry={retryWorkspaces}
    />
  );
}

function AuthPanel({
  busy,
  error,
  theme,
  onToggleTheme,
  onSubmit
}: {
  busy: boolean;
  error: string;
  theme: string;
  onToggleTheme: () => void;
  onSubmit: (mode: AuthMode, email: string, password: string, name?: string) => Promise<void>;
}) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(mode, email.trim(), password, mode === "register" ? name.trim() : undefined);
    setPassword("");
  }

  return (
    <main className="onboarding">
      <section className="onboardingCard" aria-labelledby="auth-title">
        <div className="authTop">
          <Link className="authBrand" href="/">
            TradePilot <em>AI</em>
          </Link>
          <button type="button" className="ghostButton" onClick={onToggleTheme}>
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </div>
        <p className="eyebrow">Paper trading</p>
        <h1 id="auth-title">{mode === "login" ? "Log in" : "Create account"}</h1>
        <p className="onboardingIntro">
          {mode === "login"
            ? "Enter your email and password to open your desk."
            : "Just a few details — same simple start as apps like Groww or Binance."}
        </p>
        {error && (
          <div className="message error" role="alert">
            {error}
          </div>
        )}
        <form onSubmit={submit}>
          {mode === "register" && (
            <>
              <label htmlFor="full-name">Full name</label>
              <input
                id="full-name"
                name="name"
                type="text"
                autoComplete="name"
                required
                minLength={2}
                maxLength={80}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Your name"
              />
            </>
          )}
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@email.com"
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            minLength={8}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={mode === "register" ? "At least 8 characters" : "Password"}
          />
          {mode === "register" && <small>Minimum 8 characters. You can add more profile details later in Account.</small>}
          <button className="primary" type="submit" disabled={busy}>
            {busy ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
        <button
          className="switchButton"
          type="button"
          disabled={busy}
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "New here? Create an account" : "Already have an account? Log in"}
        </button>
      </section>
    </main>
  );
}

function WorkspacePanel({
  items,
  busy,
  error,
  theme,
  onToggleTheme,
  onSelect,
  onCreate,
  onLogout,
  onRetry
}: {
  items: Array<{ workspace: { id: string; name: string }; role: string }>;
  busy: boolean;
  error: string;
  theme: string;
  onToggleTheme: () => void;
  onSelect: (id: string) => void;
  onCreate: (name: string) => Promise<void>;
  onLogout: () => void;
  onRetry: () => void;
}) {
  const [name, setName] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCreate(name);
    setName("");
  }

  return (
    <main className="onboarding">
      <section className="onboardingCard wideOnboarding" aria-labelledby="workspace-title">
        <div className="panelTitle">
          <div>
            <p className="eyebrow">Almost there</p>
            <h1 id="workspace-title">Name your desk</h1>
            <p className="onboardingIntro">One workspace is enough to start. You can switch later from Account.</p>
          </div>
          <div className="topActions">
            <button type="button" className="ghostButton" onClick={onToggleTheme}>
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <button className="textButton" type="button" onClick={onLogout}>
              Log out
            </button>
          </div>
        </div>
        {error && (
          <div className="message error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={onRetry}>
              Retry
            </button>
          </div>
        )}
        {busy && (
          <div className="message" role="status">
            Loading…
          </div>
        )}
        {items.length > 0 && (
          <ul className="workspaceList" aria-label="Available workspaces">
            {items.map(({ workspace, role }) => (
              <li key={workspace.id}>
                <button type="button" onClick={() => onSelect(workspace.id)} disabled={busy}>
                  <span>
                    <strong>{workspace.name}</strong>
                    <small>{role}</small>
                  </span>
                  <span aria-hidden="true">→</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        <form className="createWorkspace" onSubmit={submit}>
          <label htmlFor="workspace-name">Desk name</label>
          <div>
            <input
              id="workspace-name"
              required
              maxLength={80}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="My trading desk"
            />
            <button className="primary" type="submit" disabled={busy}>
              Continue
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
