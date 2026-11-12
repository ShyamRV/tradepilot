export default function PrivacyPage() {
  return (
    <article className="legalDoc">
      <p className="eyebrow">Legal</p>
      <h2>Privacy Policy</h2>
      <p className="legalLead">
        This draft describes how Athena (&quot;Athena&quot;, &quot;we&quot;, &quot;us&quot;) intends to handle
        information when you use the research and paper-trading workspace. It is a product draft for launch readiness and
        should be reviewed by counsel before production publication.
      </p>
      <p className="legalMeta">Last updated: 10 November 2026 · Draft for review</p>

      <section>
        <h3>1. Scope</h3>
        <p>
          Athena provides educational market research tools, strategy evaluation, and paper (simulated) trading for
          NSE cash equities. We do not operate a brokerage, hold customer funds, or provide investment advice. This
          policy covers the web application, related APIs, and support channels.
        </p>
      </section>

      <section>
        <h3>2. Information we collect</h3>
        <ul>
          <li>
            <strong>Account details</strong> — email address and authentication credentials you submit when registering
            or signing in (when an API backend is configured).
          </li>
          <li>
            <strong>Workspace data</strong> — workspace names, strategy settings, watchlists, paper orders, and analysis
            runs you create in the product.
          </li>
          <li>
            <strong>Technical logs</strong> — browser type, approximate region, request timestamps, and error diagnostics
            needed to operate and secure the service.
          </li>
          <li>
            <strong>Support messages</strong> — content you send when contacting support.
          </li>
        </ul>
        <p>
          In demo mode (when no API URL is configured), sample data stays in your browser session and is not uploaded to
          Athena servers.
        </p>
      </section>

      <section>
        <h3>3. How we use information</h3>
        <ul>
          <li>Authenticate sessions and maintain your workspace.</li>
          <li>Deliver delayed / end-of-day research views and paper-trading simulations.</li>
          <li>Respond to support requests and improve reliability and security.</li>
          <li>Meet legal obligations where applicable.</li>
        </ul>
        <p>We do not sell personal information. We do not use your account data to place live brokerage orders.</p>
      </section>

      <section>
        <h3>4. Market data</h3>
        <p>
          Quotes and historical series shown in Athena are delayed or end-of-day research inputs from configured
          providers. They are not real-time trading feeds. Data freshness notices in the product supersede any stale
          figures you may see elsewhere.
        </p>
      </section>

      <section>
        <h3>5. Retention and security</h3>
        <p>
          We retain account and workspace records while your account remains active and for a limited period afterward
          as needed for security, dispute resolution, and legal compliance. We apply industry-standard safeguards for
          transmission and storage; no method is perfectly secure.
        </p>
      </section>

      <section>
        <h3>6. Your choices</h3>
        <p>
          You may request access, correction, or deletion of account information by contacting support. Browser session
          storage can be cleared locally at any time. Theme preferences are stored only on your device.
        </p>
      </section>

      <section>
        <h3>7. Contact</h3>
        <p>
          Privacy questions: use the{" "}
          <a href="/support">Support</a> page. Do not send passwords or brokerage credentials in email.
        </p>
      </section>
    </article>
  );
}
