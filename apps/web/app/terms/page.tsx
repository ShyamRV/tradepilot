export default function TermsPage() {
  return (
    <article className="legalDoc">
      <p className="eyebrow">Legal</p>
      <h2>Terms of Use</h2>
      <p className="legalLead">
        These draft terms govern access to TradePilot AI. They are written for launch readiness and must be reviewed by
        counsel before binding production use. By using the product you acknowledge the research-only, paper-trading
        nature of the service.
      </p>
      <p className="legalMeta">Last updated: 10 November 2026 · Draft for review</p>

      <section>
        <h3>1. Service description</h3>
        <p>
          TradePilot is a research and simulation workspace for NSE cash equities. Features may include watchlists,
          strategy configuration, rule-based analysis, risk sizing helpers, paper portfolios, and illustrative
          backtests. TradePilot is <strong>not</strong> a stock broker, investment adviser, portfolio manager, or
          fund.
        </p>
      </section>

      <section>
        <h3>2. Paper trading only</h3>
        <p>
          All orders and positions in TradePilot are simulated. The product does not transmit live orders to exchanges
          or brokers and does not hold customer money or securities. Any returns, hit rates, or equity curves are
          educational or illustrative under stated assumptions and may differ materially from live trading.
        </p>
      </section>

      <section>
        <h3>3. Not investment advice</h3>
        <p>
          Content in TradePilot — including signals, rule pass/fail results, risk notes, charts, and notifications —
          is for informational and educational purposes only. It is not a recommendation to buy, sell, or hold any
          security. You remain solely responsible for your investment decisions.
        </p>
      </section>

      <section>
        <h3>4. Data limitations</h3>
        <p>
          Market data may be delayed, end-of-day, adjusted, incomplete, or illustrative (especially in demo mode). Do
          not rely on TradePilot figures as a substitute for licensed real-time quotes or professional execution systems.
        </p>
      </section>

      <section>
        <h3>5. Acceptable use</h3>
        <ul>
          <li>Do not attempt unauthorized access to systems, accounts, or data.</li>
          <li>Do not misuse the product to misrepresent simulated results as live performance.</li>
          <li>Do not reverse engineer or overload the service beyond ordinary use.</li>
          <li>Comply with applicable securities and technology laws in your jurisdiction.</li>
        </ul>
      </section>

      <section>
        <h3>6. Accounts</h3>
        <p>
          When authentication is enabled, you must provide accurate registration details and keep credentials
          confidential. We may suspend access for security incidents, abuse, or legal risk.
        </p>
      </section>

      <section>
        <h3>7. Disclaimer of warranties</h3>
        <p>
          The service is provided &quot;as is&quot; and &quot;as available&quot; without warranties of any kind, whether
          express or implied, including merchantability, fitness for a particular purpose, and non-infringement. We do
          not warrant uninterrupted availability or error-free analysis.
        </p>
      </section>

      <section>
        <h3>8. Limitation of liability</h3>
        <p>
          To the fullest extent permitted by law, TradePilot and its contributors are not liable for trading losses,
          missed opportunities, data inaccuracies, or consequential damages arising from use of the product. Your sole
          remedy for dissatisfaction is to stop using the service.
        </p>
      </section>

      <section>
        <h3>9. Changes</h3>
        <p>
          We may update these terms as the product evolves. Material changes will be reflected by updating the date
          above. Continued use after changes constitutes acceptance of the revised draft terms once they are finalized
          for production.
        </p>
      </section>

      <section>
        <h3>10. Contact</h3>
        <p>
          Questions about these terms: see <a href="/support">Support</a>.
        </p>
      </section>
    </article>
  );
}
