"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button, Input, Card } from "@/components/ui";

export function AuthPage() {
  const { login, signup } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        await login({ email, password });
      } else {
        await signup({ email, password });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <div className="w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Job Application Agent
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Autonomous job search & apply at scale
          </p>
        </div>

        <Card>
          {/* Tab Switcher */}
          <div className="flex mb-6 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                isLogin
                  ? "bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm"
                  : "text-gray-500 dark:text-gray-400"
              }`}
              onClick={() => setIsLogin(true)}
            >
              Sign In
            </button>
            <button
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                !isLogin
                  ? "bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 shadow-sm"
                  : "text-gray-500 dark:text-gray-400"
              }`}
              onClick={() => setIsLogin(false)}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              size="lg"
              loading={loading}
            >
              {isLogin ? "Sign In" : "Create Account"}
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-6">
          Built for the Impact Summit Hackathon
        </p>
      </div>
    </div>
  );
}
