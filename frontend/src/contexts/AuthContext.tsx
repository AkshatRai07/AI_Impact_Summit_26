"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import type { User, UserAuth } from "@/types";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: UserAuth) => Promise<void>;
  signup: (data: UserAuth) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "job_agent_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user from storage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsedUser = JSON.parse(stored) as User;
        if (parsedUser.access_token) {
          setUser(parsedUser);
          api.setToken(parsedUser.access_token);
        }
      }
    } catch (e) {
      console.error("Failed to load user from storage:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (data: UserAuth) => {
    const loggedInUser = await api.login(data);
    setUser(loggedInUser);
    if (loggedInUser.access_token) {
      api.setToken(loggedInUser.access_token);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedInUser));
  }, []);

  const signup = useCallback(async (data: UserAuth) => {
    const newUser = await api.signup(data);
    setUser(newUser);
    if (newUser.access_token) {
      api.setToken(newUser.access_token);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    api.setToken(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
