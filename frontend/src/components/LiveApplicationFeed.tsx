"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardHeader, Button, Progress } from "@/components/ui";
import { api } from "@/lib/api";

interface LiveApplication {
  job_id: string;
  job_title: string;
  company: string;
  status: "processing" | "submitted" | "failed" | "skipped";
  tailored_cover_letter?: string;
  tailored_resume?: Record<string, unknown>;
  confirmation_id?: string;
  error_message?: string;
  timestamp: Date;
}

interface LiveApplicationFeedProps {
  userId: string;
  isRunning: boolean;
  onWorkflowEnd: () => void;
}

export function LiveApplicationFeed({
  userId,
  isRunning,
  onWorkflowEnd,
}: LiveApplicationFeedProps) {
  const [connected, setConnected] = useState(false);
  const [applications, setApplications] = useState<LiveApplication[]>([]);
  const [currentJob, setCurrentJob] = useState<{ title: string; company: string } | null>(null);
  const [totalJobs, setTotalJobs] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [totalSubmitted, setTotalSubmitted] = useState(0);
  const [totalFailed, setTotalFailed] = useState(0);
  const [workflowStatus, setWorkflowStatus] = useState<"running" | "completed" | "failed">("running");
  const [error, setError] = useState<string | null>(null);
  const [stageMessage, setStageMessage] = useState<string>("🔄 Starting...");
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!isRunning || !userId) {
      return;
    }

    const streamUrl = api.getWorkflowStreamUrl(userId);
    console.log("[SSE] Connecting to:", streamUrl);

    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log("[SSE] Connected");
      setConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      console.log("[SSE] Event:", event.data);

      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "workflow_started":
            setWorkflowStatus("running");
            if (data.stage_message) setStageMessage(data.stage_message);
            break;

          case "stage_update":
            if (data.stage_message) setStageMessage(data.stage_message);
            break;

          case "jobs_fetched":
            setTotalJobs(data.total_jobs || 0);
            if (data.stage_message) setStageMessage(data.stage_message);
            break;

          case "job_processing":
            setCurrentJob({
              title: data.job?.title || "Unknown",
              company: data.job?.company || "Unknown",
            });
            setCurrentIndex(data.current_index || 0);
            setTotalJobs(data.total_jobs || totalJobs);
            if (data.stage_message) setStageMessage(data.stage_message);
            // Add to applications as processing - use job.id as job_id
            const jobId = data.job?.id || data.job?.job_id || `job-${Date.now()}`;
            setApplications((prev) => {
              // Check if already exists
              if (prev.some(a => a.job_id === jobId)) {
                return prev;
              }
              return [
                ...prev,
                {
                  job_id: jobId,
                  job_title: data.job?.title || "Unknown",
                  company: data.job?.company || "Unknown",
                  status: "processing",
                  tailored_cover_letter: data.tailored_cover_letter,
                  tailored_resume: data.tailored_resume,
                  timestamp: new Date(),
                },
              ];
            });
            break;

          case "application_result":
            console.log("[SSE] Application result:", data);
            setCurrentIndex(data.current_index || currentIndex);
            setTotalJobs(data.total_jobs || totalJobs);
            if (data.stage_message) setStageMessage(data.stage_message);
            
            // Get the job_id from the application result
            const resultJobId = data.application?.job_id;
            console.log("[SSE] Updating job_id:", resultJobId, "with status:", data.status);
            
            // Update application status and count submitted/failed from applications array
            setApplications((prev) => {
              const updated = prev.map((app): LiveApplication => {
                if (app.job_id === resultJobId) {
                  const newStatus: LiveApplication["status"] = data.status === "submitted" ? "submitted" : "failed";
                  return {
                    ...app,
                    status: newStatus,
                    confirmation_id: data.application?.confirmation_id,
                    error_message: data.application?.error_message,
                    tailored_cover_letter: data.application?.cover_letter || app.tailored_cover_letter,
                  };
                }
                return app;
              });
              console.log("[SSE] Applications after update:", updated);
              
              // Count submitted and failed from the updated applications array
              const submittedCount = updated.filter(a => a.status === "submitted").length;
              const failedCount = updated.filter(a => a.status === "failed").length;
              setTotalSubmitted(submittedCount);
              setTotalFailed(failedCount);
              
              return updated;
            });
            setCurrentJob(null);
            break;

          case "job_skipped":
            setCurrentIndex(data.current_index || currentIndex);
            setTotalJobs(data.total_jobs || totalJobs);
            if (data.stage_message) setStageMessage(data.stage_message);
            // Update last processing app to skipped
            setApplications((prev) => {
              const lastProcessing = [...prev].reverse().find((a) => a.status === "processing");
              if (lastProcessing) {
                return prev.map((app) =>
                  app.job_id === lastProcessing.job_id ? { ...app, status: "skipped" } : app
                );
              }
              return prev;
            });
            setCurrentJob(null);
            break;

          case "workflow_completed":
            setWorkflowStatus("completed");
            setTotalSubmitted(data.total_submitted || 0);
            setTotalFailed(data.total_failed || 0);
            setStageMessage("🎉 Workflow completed!");
            onWorkflowEnd();
            break;

          case "workflow_failed":
            setWorkflowStatus("failed");
            setError(data.error || "Workflow failed");
            onWorkflowEnd();
            break;
        }
      } catch (e) {
        console.error("[SSE] Parse error:", e);
      }
    };

    eventSource.onerror = () => {
      console.error("[SSE] Connection error");
      setConnected(false);
    };

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [isRunning, userId, onWorkflowEnd, currentIndex, totalJobs]);

  const handleKill = async () => {
    try {
      await api.killWorkflow(userId);
      onWorkflowEnd();
    } catch (err) {
      console.error("Kill failed:", err);
    }
  };

  // Don't show anything if not running and no applications
  if (!isRunning && applications.length === 0) {
    return null;
  }

  const progress = totalJobs > 0 ? (currentIndex / totalJobs) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <Card>
        <CardHeader
          title="Live Application Feed"
          description={
            connected
              ? "🟢 Connected - Real-time updates"
              : isRunning
              ? "⏳ Connecting..."
              : workflowStatus === "completed"
              ? "✅ Workflow completed"
              : "❌ Workflow ended"
          }
          action={
            isRunning && (
              <Button variant="danger" size="sm" onClick={handleKill}>
                🛑 Stop
              </Button>
            )
          }
        />

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Live Stage Message */}
        {isRunning && (
          <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
            <p className="text-lg font-medium text-blue-800 dark:text-blue-200 animate-pulse">
              {stageMessage}
            </p>
          </div>
        )}

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-500">
            <span>Progress</span>
            <span>
              {currentIndex} / {totalJobs} jobs
            </span>
          </div>
          <Progress value={progress} showLabel />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p className="text-2xl font-bold text-green-600">{totalSubmitted}</p>
            <p className="text-xs text-gray-500">Submitted</p>
          </div>
          <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p className="text-2xl font-bold text-red-600">{totalFailed}</p>
            <p className="text-xs text-gray-500">Failed</p>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {Math.max(0, totalJobs - currentIndex)}
            </p>
            <p className="text-xs text-gray-500">Remaining</p>
          </div>
        </div>
      </Card>

      {/* Applications List */}
      {applications.length > 0 && (
        <Card>
          <CardHeader title="Applications" description={`${applications.length} processed`} />
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {applications
              .slice()
              .reverse()
              .map((app, i) => (
                <ApplicationCard key={`${app.job_id}-${i}`} application={app} />
              ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function ApplicationCard({ application }: { application: LiveApplication }) {
  const [showDetails, setShowDetails] = useState(false);

  const statusStyles = {
    processing: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    submitted: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    failed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    skipped: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
  };

  const statusLabels = {
    processing: "⏳ Processing",
    submitted: "✅ Submitted",
    failed: "❌ Failed",
    skipped: "⏭️ Skipped",
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">{application.job_title}</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">{application.company}</p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[application.status]}`}>
          {statusLabels[application.status]}
        </span>
      </div>

      {/* Confirmation ID for submitted */}
      {application.confirmation_id && (
        <p className="mt-2 text-xs text-gray-500">
          Confirmation: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">{application.confirmation_id}</code>
        </p>
      )}

      {/* Error message for failed */}
      {application.error_message && (
        <p className="mt-2 text-xs text-red-500">{application.error_message}</p>
      )}

      {/* Toggle for personalized content */}
      {application.tailored_cover_letter && (
        <div className="mt-3">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {showDetails ? "Hide" : "Show"} Personalized Application
          </button>
          {showDetails && (
            <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
              <p className="font-medium mb-2">Cover Letter:</p>
              {application.tailored_cover_letter}
            </div>
          )}
        </div>
      )}

      <p className="mt-2 text-xs text-gray-400">{application.timestamp.toLocaleTimeString()}</p>
    </div>
  );
}
