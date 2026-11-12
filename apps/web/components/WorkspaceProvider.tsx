"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  AuthMode,
  DashboardData,
  WorkspaceMembership,
  apiConfigured,
  authenticate,
  createWorkspace,
  demoDashboard,
  getDashboard,
  listWorkspaces,
  logout
} from "@/lib/api";

type Session = { token: string; workspaceId: string };
type Gate = "boot" | "auth" | "workspaces" | "ready";

type WorkspaceContextValue = {
  apiConfigured: boolean;
  gate: Gate;
  data: DashboardData | null;
  busy: boolean;
  error: string;
  workspaces: WorkspaceMembership[];
  handleAuth: (mode: AuthMode, email: string, password: string) => Promise<void>;
  handleCreate: (name: string) => Promise<void>;
  handleSelect: (id: string) => void;
  handleLogout: () => void;
  reload: () => void;
  retryWorkspaces: () => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);
const SESSION_KEY = "tradepilot.session";

function saveSession(session: Session | null) {
  if (session) sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  else sessionStorage.removeItem(SESSION_KEY);
}

function readSession(): Session | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(SESSION_KEY) ?? "null") as Partial<Session> | null;
    return value && typeof value.token === "string" && typeof value.workspaceId === "string"
      ? { token: value.token, workspaceId: value.workspaceId }
      : null;
  } catch {
    sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [gate, setGate] = useState<Gate>(apiConfigured ? "boot" : "ready");
  const [data, setData] = useState<DashboardData | null>(apiConfigured ? null : demoDashboard);
  const [token, setToken] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [workspaces, setWorkspaces] = useState<WorkspaceMembership[]>([]);
  const [busy, setBusy] = useState(apiConfigured);
  const [error, setError] = useState("");

  async function loadWorkspaceList(activeToken: string) {
    setBusy(true);
    setError("");
    setGate("workspaces");
    try {
      const items = await listWorkspaces(activeToken);
      setWorkspaces(items);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        saveSession(null);
        setToken("");
        setGate("auth");
      }
      setError(reason instanceof Error ? reason.message : "Unable to load workspaces.");
    } finally {
      setBusy(false);
    }
  }

  async function loadDashboard(activeToken: string, activeWorkspaceId: string) {
    setBusy(true);
    setError("");
    try {
      const result = await getDashboard(activeToken, activeWorkspaceId);
      setData(result);
      setGate("ready");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        saveSession(null);
        setToken("");
        setWorkspaceId("");
        setGate("auth");
      }
      setError(reason instanceof Error ? reason.message : "Unable to load the dashboard.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!apiConfigured) return;
    const stored = readSession();
    if (!stored) {
      setBusy(false);
      setGate("auth");
      return;
    }
    setToken(stored.token);
    setWorkspaceId(stored.workspaceId);
    const controller = new AbortController();
    (async () => {
      try {
        const items = await listWorkspaces(stored.token, controller.signal);
        setWorkspaces(items);
        const selected = items.some((item) => item.workspace.id === stored.workspaceId) ? stored.workspaceId : "";
        if (selected) {
          setWorkspaceId(selected);
          const result = await getDashboard(stored.token, selected, controller.signal);
          setData(result);
          setGate("ready");
        } else {
          saveSession({ token: stored.token, workspaceId: "" });
          setGate("workspaces");
        }
      } catch (reason) {
        if ((reason as Error).name === "AbortError") return;
        if (reason instanceof ApiError && reason.status === 401) {
          saveSession(null);
          setToken("");
          setGate("auth");
        } else {
          setError(reason instanceof Error ? reason.message : "Unable to restore the session.");
          setGate(stored.workspaceId ? "ready" : "workspaces");
        }
      } finally {
        setBusy(false);
      }
    })();
    return () => controller.abort();
  }, []);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      apiConfigured,
      gate,
      data,
      busy,
      error,
      workspaces,
      handleAuth: async (mode, email, password) => {
        setBusy(true);
        setError("");
        try {
          const nextToken = await authenticate(mode, email, password);
          setToken(nextToken);
          saveSession({ token: nextToken, workspaceId: "" });
          await loadWorkspaceList(nextToken);
        } catch (reason) {
          setError(reason instanceof Error ? reason.message : "Authentication failed.");
          setBusy(false);
        }
      },
      handleCreate: async (name) => {
        setBusy(true);
        setError("");
        try {
          const workspace = await createWorkspace(token, name);
          setWorkspaces((items) => [...items, { workspace, role: "owner" }]);
          setWorkspaceId(workspace.id);
          setData(null);
          saveSession({ token, workspaceId: workspace.id });
          await loadDashboard(token, workspace.id);
        } catch (reason) {
          setError(reason instanceof Error ? reason.message : "Unable to create workspace.");
          setBusy(false);
        }
      },
      handleSelect: (id) => {
        setWorkspaceId(id);
        setData(null);
        saveSession({ token, workspaceId: id });
        void loadDashboard(token, id);
      },
      handleLogout: () => {
        const activeToken = token;
        saveSession(null);
        setToken("");
        setWorkspaceId("");
        setData(null);
        setWorkspaces([]);
        setError("");
        setGate("auth");
        if (activeToken) void logout(activeToken).catch(() => undefined);
      },
      reload: () => {
        if (token && workspaceId) void loadDashboard(token, workspaceId);
      },
      retryWorkspaces: () => {
        if (token) void loadWorkspaceList(token);
      }
    }),
    [busy, data, error, gate, token, workspaceId, workspaces]
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return context;
}
