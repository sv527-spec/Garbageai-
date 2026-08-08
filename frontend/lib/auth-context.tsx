"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { apiFetch } from "./api";

type User = {
  id: string;
  email: string;
  full_name: string;
  role: "worker" | "supervisor" | "user" | "admin";
  language_pref: string;
};

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: Record<string, unknown>) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = window.localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch<User>("/users/me")
      .then(setUser)
      .catch(() => window.localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      auth: false,
    });
    window.localStorage.setItem("access_token", tokens.access_token);
    window.localStorage.setItem("refresh_token", tokens.refresh_token);
    const me = await apiFetch<User>("/users/me");
    setUser(me);
  }

  async function register(payload: Record<string, unknown>) {
    await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      auth: false,
    });
    await login(payload.email as string, payload.password as string);
  }

  function logout() {
    window.localStorage.removeItem("access_token");
    window.localStorage.removeItem("refresh_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
