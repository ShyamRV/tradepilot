"use client";

import Link from "next/link";
import { useTheme } from "@/components/ThemeProvider";
import { useWorkspace } from "@/components/WorkspaceProvider";

export default function AccountPage() {
  const { data, apiConfigured, profile, workspaces, workspaceId, handleLogout, handleSelect } = useWorkspace();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="stack accountPage">
      <header className="sectionHero">
        <div>
          <p className="eyebrow">Your account</p>
          <h2>Profile & settings</h2>
          <p>Manage identity, workspace, and desk preferences. Paper trading stays on for this release.</p>
        </div>
      </header>

      <section className="accountGrid">
        <article className="panel">
          <header className="panelHeader">
            <h2>Profile</h2>
            <span className="pill">{apiConfigured ? "Signed in" : "Demo"}</span>
          </header>
          <dl className="metaList">
            <div>
              <dt>Display name</dt>
              <dd>{profile?.name || "—"}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{profile?.email || (apiConfigured ? "—" : "demo@tradepilot.local")}</dd>
            </div>
            <div>
              <dt>Account type</dt>
              <dd>Paper trading</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>{apiConfigured ? "Live API session" : "Local demo session"}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <header className="panelHeader">
            <h2>Workspace</h2>
          </header>
          <dl className="metaList">
            <div>
              <dt>Active desk</dt>
              <dd>{data?.workspace.name ?? "—"}</dd>
            </div>
            <div>
              <dt>Market</dt>
              <dd>{data?.workspace.market ?? "NSE cash equities"}</dd>
            </div>
            <div>
              <dt>Execution</dt>
              <dd>{data?.workspace.mode ?? "Paper trading"}</dd>
            </div>
            <div>
              <dt>Workspace ID</dt>
              <dd className="monoValue">{workspaceId || "demo"}</dd>
            </div>
          </dl>
          {apiConfigured && workspaces.length > 1 && (
            <div className="accountSwitchList">
              <p className="eyebrow">Switch workspace</p>
              <ul>
                {workspaces.map((item) => (
                  <li key={item.workspace.id}>
                    <button
                      type="button"
                      className={item.workspace.id === workspaceId ? "active" : ""}
                      onClick={() => handleSelect(item.workspace.id)}
                    >
                      <strong>{item.workspace.name}</strong>
                      <span>{item.role}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>

        <article className="panel">
          <header className="panelHeader">
            <h2>Preferences</h2>
          </header>
          <div className="accountActions">
            <div className="preferenceRow">
              <div>
                <strong>Appearance</strong>
                <span>Light or dark desk theme</span>
              </div>
              <button type="button" className="ghostButton" onClick={toggleTheme}>
                {theme === "dark" ? "Use light" : "Use dark"}
              </button>
            </div>
            <div className="preferenceRow">
              <div>
                <strong>Paper mode</strong>
                <span>Live broker linking stays gated off</span>
              </div>
              <span className="pill good">On</span>
            </div>
            <div className="preferenceRow">
              <div>
                <strong>Risk disclosures</strong>
                <span>Shown next to agent performance</span>
              </div>
              <span className="pill good">On</span>
            </div>
          </div>
        </article>

        <article className="panel">
          <header className="panelHeader">
            <h2>Quick links</h2>
          </header>
          <div className="accountLinks">
            <Link href="/playground">Playground</Link>
            <Link href="/portfolio">Portfolio</Link>
            <Link href="/agents">AI agents</Link>
            <Link href="/markets">Markets</Link>
            <Link href="/support">Support</Link>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
          </div>
          {apiConfigured && (
            <button type="button" className="dangerButton accountLogout" onClick={handleLogout}>
              Log out
            </button>
          )}
        </article>
      </section>
    </div>
  );
}
