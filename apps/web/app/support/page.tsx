export default function SupportPage() {
  return (
    <article className="legalDoc">
      <p className="eyebrow">Help</p>
      <h2>Support</h2>
      <p className="legalLead">
        TradePilot AI is a paper-trading research desk. Use this page for product help, data freshness questions, and
        account issues. We cannot place live broker orders or provide personalized investment advice.
      </p>
      <p className="legalMeta">Support hours (draft): Mon–Fri 10:00–18:00 IST · Response within 1–2 business days</p>

      <section>
        <h3>Before you write</h3>
        <ul>
          <li>
            Confirm the honesty banner: <strong>Paper trading only · Not investment advice</strong>.
          </li>
          <li>
            Open <strong>Account</strong> for your profile, workspace, and preferences.
          </li>
          <li>
            Analysis shows rule pass/fail counts, not probability of profit. Backtest returns are illustrative demo
            assumptions.
          </li>
        </ul>
      </section>

      <section>
        <h3>Contact</h3>
        <dl className="metaList">
          <div>
            <dt>Email</dt>
            <dd>
              <a href="mailto:support@tradepilot.example">support@tradepilot.example</a> (placeholder — replace before
              launch)
            </dd>
          </div>
          <div>
            <dt>Include</dt>
            <dd>Workspace name, approximate time of the issue, browser, and whether API mode or demo mode is active.</dd>
          </div>
          <div>
            <dt>Do not send</dt>
            <dd>Passwords, API keys, brokerage credentials, or government ID scans.</dd>
          </div>
        </dl>
      </section>

      <section>
        <h3>Common topics</h3>
        <ul>
          <li>
            <strong>Demo vs connected API</strong> — Without an API URL the app runs on built-in sample data. Configure{" "}
            <code>NEXT_PUBLIC_API_URL</code> to authenticate against your backend.
          </li>
          <li>
            <strong>Paper fills</strong> — Simulated next-session open fills; no live exchange routing.
          </li>
          <li>
            <strong>Privacy &amp; terms</strong> — Review the draft{" "}
            <a href="/privacy">Privacy Policy</a> and <a href="/terms">Terms of Use</a>.
          </li>
          <li>
            <strong>Theme</strong> — Dark and light modes are available from the sidebar or top bar.
          </li>
        </ul>
      </section>

      <section>
        <h3>Status &amp; limitations</h3>
        <p>
          TradePilot does not guarantee uninterrupted service. Market data may be delayed or incomplete. Simulated
          performance is not a promise of future results. For urgent security concerns, email support with
          &quot;SECURITY&quot; in the subject line.
        </p>
      </section>
    </article>
  );
}
