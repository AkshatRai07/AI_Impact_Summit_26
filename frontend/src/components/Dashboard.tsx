"use client";

import { useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useStudentProfile, useApplyPolicy } from "@/hooks";
import type { StudentProfile, WorkflowStatus } from "@/types";
import {
  ResumeUpload,
  ProfileView,
  PolicyEditor,
} from "@/components";
import { LiveApplicationFeed } from "@/components/LiveApplicationFeed";
import { Button, Card } from "@/components/ui";
import { api } from "@/lib/api";

type Step = "upload" | "review" | "policy" | "apply";

export function Dashboard() {
  const { user, logout } = useAuth();
  const { profile, setProfile, clearProfile } = useStudentProfile();
  const { policy, setPolicy } = useApplyPolicy();

  const [step, setStep] = useState<Step>(profile ? "review" : "upload");
  const [uploading, setUploading] = useState(false);
  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false);
  const [startingWorkflow, setStartingWorkflow] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadComplete = useCallback(
    (profileData: unknown) => {
      setProfile(profileData as StudentProfile);
      setStep("review");
    },
    [setProfile]
  );

  const handleStartWorkflow = async () => {
    if (!user || !profile) return;

    setStartingWorkflow(true);
    setWorkflowError(null);

    try {
      await api.startWorkflow({
        user_id: user.id,
        student_profile: profile,
        bullet_bank: profile.bullet_bank,
        answer_library: profile.answer_library,
        proof_pack: profile.proof_pack,
        apply_policy: policy,
      });

      setIsWorkflowRunning(true);
      setStep("apply");
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : "Failed to start workflow");
    } finally {
      setStartingWorkflow(false);
    }
  };

  const handleWorkflowStatusChange = useCallback((status: WorkflowStatus | null) => {
    if (status && status.status !== "running") {
      setRefreshTrigger((prev) => prev + 1);
    }
  }, []);

  const handleReset = () => {
    clearProfile();
    setStep("upload");
    setIsWorkflowRunning(false);
  };

  const handleClearApplications = async () => {
    if (!user) return;
    if (!confirm("Are you sure you want to clear all applications? This will allow you to re-apply to all jobs.")) {
      return;
    }
    try {
      await api.clearApplications(user.id);
      setRefreshTrigger((prev) => prev + 1);
      alert("Applications cleared! You can now run the workflow again.");
    } catch (err) {
      alert("Failed to clear applications: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const steps: { id: Step; label: string; icon: string }[] = [
    { id: "upload", label: "Upload", icon: "📄" },
    { id: "review", label: "Profile", icon: "👤" },
    { id: "policy", label: "Policy", icon: "⚙️" },
    { id: "apply", label: "Apply", icon: "🚀" },
  ];

  const canNavigateTo = (targetStep: Step): boolean => {
    if (targetStep === "upload") return true;
    if (!profile) return false;
    if (targetStep === "review") return true;
    if (targetStep === "policy") return true;
    if (targetStep === "apply") return true;
    return false;
  };

  return (
    <div className="min-h-screen bg-[#09090b] relative overflow-hidden">
      {/* Background FX */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(#334155 1px, transparent 1px)', backgroundSize: '32px 32px' }}>
      </div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[100px] pointer-events-none"></div>

      {/* Header */}
      <header className="relative z-10 bg-[#121214]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <span className="font-bold text-white text-lg">
                Arbeit
              </span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-400 hidden sm:block">
                {user?.email}
              </span>
              <Button variant="ghost" size="sm" onClick={handleClearApplications}>
                🗑️ Clear
              </Button>
              <Button variant="ghost" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Step Navigation */}
      <nav className="relative z-10 bg-[#121214]/60 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-1 sm:gap-2 py-3 overflow-x-auto">
            {steps.map((s, index) => {
              const isActive = s.id === step;
              const canNavigate = canNavigateTo(s.id);

              return (
                <button
                  key={s.id}
                  onClick={() => canNavigate && setStep(s.id)}
                  disabled={!canNavigate}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? "bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border border-blue-500/30"
                      : canNavigate
                      ? "text-slate-400 hover:text-white hover:bg-white/5"
                      : "text-slate-600 cursor-not-allowed"
                  }`}
                >
                  <span>{s.icon}</span>
                  <span className="hidden sm:inline">{s.label}</span>
                  {index < steps.length - 1 && (
                    <svg
                      className="w-4 h-4 text-slate-600 hidden sm:block ml-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="space-y-6">
          {/* Upload Step */}
          {step === "upload" && (
            <ResumeUpload
              onUploadComplete={handleUploadComplete}
              uploading={uploading}
              setUploading={setUploading}
            />
          )}

          {/* Review Step */}
          {step === "review" && profile && (
            <div className="space-y-6">
              <ProfileView profile={profile} />
              <div className="flex gap-4">
                <Button variant="secondary" onClick={handleReset}>
                  Upload New Resume
                </Button>
                <Button variant="gradient" onClick={() => setStep("policy")}>
                  Continue to Policy →
                </Button>
              </div>
            </div>
          )}

          {/* Policy Step */}
          {step === "policy" && (
            <div className="space-y-6">
              <PolicyEditor
                policy={policy}
                onChange={setPolicy}
                disabled={isWorkflowRunning}
              />
              <div className="flex gap-4">
                <Button variant="secondary" onClick={() => setStep("review")}>
                  ← Back to Profile
                </Button>
                <Button variant="gradient" onClick={() => setStep("apply")}>
                  Continue to Apply →
                </Button>
              </div>
            </div>
          )}

          {/* Apply Step */}
          {step === "apply" && user && (
            <div className="space-y-6">
              {/* Start Workflow Card */}
              {!isWorkflowRunning && (
                <Card glow>
                  <div className="text-center py-10">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl mb-6 border border-white/10">
                      <span className="text-4xl">🚀</span>
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-3">
                      Ready to Launch Autonomous Applications
                    </h2>
                    <p className="text-slate-400 mb-8 max-w-lg mx-auto leading-relaxed">
                      The AI agent will search for matching jobs, craft personalized applications,
                      and submit them automatically based on your policy preferences.
                    </p>

                    {workflowError && (
                      <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl max-w-md mx-auto backdrop-blur-sm">
                        <p className="text-sm text-red-400">
                          {workflowError}
                        </p>
                      </div>
                    )}

                    <div className="flex gap-4 justify-center">
                      <Button variant="secondary" onClick={() => setStep("policy")}>
                        ← Edit Policy
                      </Button>
                      <Button
                        variant="gradient"
                        size="lg"
                        onClick={handleStartWorkflow}
                        loading={startingWorkflow}
                        disabled={!policy.enabled}
                        className="shadow-lg shadow-blue-500/25"
                      >
                        🚀 Start Auto-Apply
                      </Button>
                    </div>

                    {!policy.enabled && (
                      <p className="text-sm text-amber-400 mt-6 flex items-center justify-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                        Policy is disabled. Enable it to start applying.
                      </p>
                    )}
                  </div>
                </Card>
              )}

              {/* Live Application Feed - shows when workflow is running */}
              <LiveApplicationFeed
                userId={user.id}
                isRunning={isWorkflowRunning}
                onWorkflowEnd={() => setIsWorkflowRunning(false)}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
