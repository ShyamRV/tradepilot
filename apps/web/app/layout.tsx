import type { Metadata } from "next";
import { IBM_Plex_Sans, Sora } from "next/font/google";
import { Providers } from "@/components/Providers";
import { AppGate } from "@/components/AppGate";
import "./globals.css";

const display = Sora({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700", "800"]
});

const body = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"]
});

export const metadata: Metadata = {
  title: "TradePilot AI",
  description: "Evidence-led NSE research, strategy analysis, and paper trading"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body className={`${display.variable} ${body.variable}`}>
        <script
          dangerouslySetInnerHTML={{
            __html: `(() => { try { const t = localStorage.getItem("tradepilot.theme"); if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; else if (window.matchMedia("(prefers-color-scheme: light)").matches) document.documentElement.dataset.theme = "light"; } catch (_) {} })();`
          }}
        />
        <Providers>
          <AppGate>{children}</AppGate>
        </Providers>
      </body>
    </html>
  );
}
