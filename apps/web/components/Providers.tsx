"use client";

import { ThemeProvider } from "@/components/ThemeProvider";
import { WorkspaceProvider } from "@/components/WorkspaceProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <WorkspaceProvider>{children}</WorkspaceProvider>
    </ThemeProvider>
  );
}
