"use client";

import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api/client";

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, displayName: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    const token = window.localStorage.getItem("nexusflow.access_token");

    const resolve = async () => {
      if (!token) return;
      try {
        const current = await api.get<AuthUser>("/auth/me");
        if (active) setUser(current);
      } catch {
        window.localStorage.removeItem("nexusflow.access_token");
      }
    };

    // Settling state in an async callback (rather than synchronously in the
    // effect body) avoids a cascading render and satisfies set-state-in-effect.
    resolve().finally(() => {
      if (active) setReady(true);
    });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const expireSession = () => {
      queryClient.clear();
      setUser(null);
      setReady(true);
    };
    window.addEventListener("nexusflow:unauthorized", expireSession);
    return () => window.removeEventListener("nexusflow:unauthorized", expireSession);
  }, [queryClient]);

  async function saveSession(path: string, payload: Record<string, string>) {
    const result = await api.post<{ access_token: string; user: AuthUser }>(path, payload);
    queryClient.clear();
    window.localStorage.setItem("nexusflow.access_token", result.access_token);
    setUser(result.user);
  }

  function logout() {
    queryClient.clear();
    window.localStorage.removeItem("nexusflow.access_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{
      user,
      ready,
      login: (email, password) => saveSession("/auth/login", { email, password }),
      register: (email, display_name, password) => saveSession("/auth/register", { email, display_name, password }),
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside Providers");
  return value;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
