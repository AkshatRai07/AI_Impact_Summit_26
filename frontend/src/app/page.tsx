"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useAuth } from "@/contexts/AuthContext";
import { AuthPage } from "@/components/AuthPage";
import { LandingPage } from "@/components/LandingPage";

// Dynamic import to prevent SSR issues
const Dashboard = dynamic(
  () => import("@/components/Dashboard").then((mod) => mod.Dashboard),
  { ssr: false }
);

export default function Home() {
  const { user, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-sm text-slate-500 mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  // Show dashboard if logged in
  if (user) {
    return <Dashboard />;
  }

  // Show auth page if user clicked "Get Started"
  if (showAuth) {
    return <AuthPage onBack={() => setShowAuth(false)} />;
  }

  // Show landing page by default
  return <LandingPage onGetStarted={() => setShowAuth(true)} />;
}
