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
type Profile = { name: string; email: string };

type WorkspaceContextValue = {
  apiConfigured: boolean;
  token: string;
  workspaceId: string;
  gate: Gate;
  data: DashboardData | null;
  busy: boolean;
  error: string;
  workspaces: WorkspaceMembership[];
  profile: Profile | null;
  handleAuth: (mode: AuthMode, email: string, password: string, name?: string) => Promise<void>;
  handleCreate: (name: string) => Promise<void>;
  handleSelect: (id: string) => void;
  handleLogout: () => void;
  reload: () => void;
  retryWorkspaces: () => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);
const SESSION_KEY = "tradepilot.session";
const PROFILE_KEY = "tradepilot.profile";

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

function saveProfile(profile: Profile | null) {
  if (profile) localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  else localStorage.removeItem(PROFILE_KEY);
}

function readProfile(): Profile | null {
  try {
    const value = JSON.parse(localStorage.getItem(PROFILE_KEY) ?? "null") as Partial<Profile> | null;
    if (!value || typeof value.email !== "string") return null;
    return { name: typeof value.name === "string" ? value.name : "", email: value.email };
  } catch {
    localStorage.removeItem(PROFILE_KEY);
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
  const [profile, setProfile] = useState<Profile | null>(null);

  async function enterWorkspace(activeToken: string, activeWorkspaceId: string) {
    setWorkspaceId(activeWorkspaceId);
    saveSession({ token: activeToken, workspaceId: activeWorkspaceId });
    await loadDashboard(activeToken, activeWorkspaceId);
  }

  async function loadWorkspaceList(activeToken: string, preferredName?: string) {
    setBusy(true);
    setError("");
    try {
      let items = await listWorkspaces(activeToken);
      if (items.length === 0) {
        const deskName = preferredName ? `${preferredName.split(" ")[0]}'s desk` : "My desk";
        const workspace = await createWorkspace(activeToken, deskName);
        items = [{ workspace, role: "owner" }];
        setWorkspaces(items);
        await enterWorkspace(activeToken, workspace.id);
        return;
      }
      setWorkspaces(items);
      if (items.length === 1) {
        await enterWorkspace(activeToken, items[0].workspace.id);
        return;
      }
      setGate("workspaces");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        saveSession(null);
        setToken("");
        setGate("auth");
      }
      setError(reason instanceof Error ? reason.message : "Unable to load workspaces.");
      setGate("workspaces");
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
    if (!apiConfigured) {
      setProfile({ name: "Demo trader", email: "demo@tradepilot.local" });
      return;
    }
    const storedProfile = readProfile();
    if (storedProfile) setProfile(storedProfile);
    const stored = readSession();
    if (!stored) {
      // Intentional one-time restoration of browser session state after hydration.
      // eslint-disable-next-line react-hooks/set-state-in-effect
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
        } else if (items.length === 1) {
          await enterWorkspace(stored.token, items[0].workspace.id);
        } else if (items.length === 0) {
          const workspace = await createWorkspace(stored.token, "My desk");
          setWorkspaces([{ workspace, role: "owner" }]);
          await enterWorkspace(stored.token, workspace.id);
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
      token,
      workspaceId,
      gate,
      data,
      busy,
      error,
      workspaces,
      profile,
      handleAuth: async (mode, email, password, name) => {
        setBusy(true);
        setError("");
        try {
          const nextToken = await authenticate(mode, email, password);
          const nextProfile = {
            email,
            name: name?.trim() || readProfile()?.name || email.split("@")[0] || "Trader"
          };
          setProfile(nextProfile);
          saveProfile(nextProfile);
          setToken(nextToken);
          saveSession({ token: nextToken, workspaceId: "" });
          await loadWorkspaceList(nextToken, nextProfile.name);
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
          setData(null);
          await enterWorkspace(token, workspace.id);
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
        if (token) void loadWorkspaceList(token, profile?.name);
      }
    }),
    [busy, data, error, gate, profile, token, workspaceId, workspaces]
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return context;
}
