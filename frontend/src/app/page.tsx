"use client";

import dynamic from "next/dynamic";
import { useAuth } from "@/contexts/AuthContext";
import { AuthPage } from "@/components/AuthPage";

// Dynamic import to prevent SSR issues
const Dashboard = dynamic(
  () => import("@/components/Dashboard").then((mod) => mod.Dashboard),
  { ssr: false }
);

export default function Home() {
  const { user, loading } = useAuth();

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-3 border-blue-600 border-t-transparent rounded-full mx-auto" />
          <p className="text-sm text-gray-500 mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  // Show auth page if not logged in
  if (!user) {
    return <AuthPage />;
  }

  // Show dashboard if logged in
  return <Dashboard />;
}
