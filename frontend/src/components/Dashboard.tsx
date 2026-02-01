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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
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
                    d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                Job Agent
              </span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                {user?.email}
              </span>
              <Button variant="secondary" size="sm" onClick={handleClearApplications}>
                🗑️ Clear Apps
              </Button>
              <Button variant="ghost" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Step Navigation */}
      <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
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
                  className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                      : canNavigate
                      ? "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
                  }`}
                >
                  <span>{s.icon}</span>
                  <span className="hidden sm:inline">{s.label}</span>
                  {index < steps.length - 1 && (
                    <svg
                      className="w-4 h-4 text-gray-300 dark:text-gray-600 hidden sm:block ml-2"
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                <Button onClick={() => setStep("policy")}>
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
                <Button onClick={() => setStep("apply")}>
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
                <Card>
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
                      <span className="text-3xl">🚀</span>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                      Ready to Start Autonomous Applications
                    </h2>
                    <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
                      The agent will search for jobs, personalize your applications,
                      and submit them automatically based on your policy.
                    </p>

                    {workflowError && (
                      <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg max-w-md mx-auto">
                        <p className="text-sm text-red-600 dark:text-red-400">
                          {workflowError}
                        </p>
                      </div>
                    )}

                    <div className="flex gap-4 justify-center">
                      <Button variant="secondary" onClick={() => setStep("policy")}>
                        ← Edit Policy
                      </Button>
                      <Button
                        size="lg"
                        onClick={handleStartWorkflow}
                        loading={startingWorkflow}
                        disabled={!policy.enabled}
                      >
                        🚀 Start Auto-Apply
                      </Button>
                    </div>

                    {!policy.enabled && (
                      <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-4">
                        ⚠️ Policy is disabled. Enable it to start applying.
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
