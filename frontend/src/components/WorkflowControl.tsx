"use client";

import { useEffect, useState, useRef } from "react";
import type { WorkflowStatus } from "@/types";
import { Card, CardHeader, Button, Progress, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";

interface WorkflowControlProps {
  userId: string;
  onStatusChange?: (status: WorkflowStatus | null) => void;
  isRunning: boolean;
  setIsRunning: (running: boolean) => void;
}

export function WorkflowControl({
  userId,
  onStatusChange,
  isRunning,
  setIsRunning,
}: WorkflowControlProps) {
  const [status, setStatus] = useState<WorkflowStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [killing, setKilling] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Poll for status when workflow is running
  useEffect(() => {
    if (!isRunning || !userId) {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      return;
    }

    const pollStatus = async () => {
      try {
        const newStatus = await api.getWorkflowStatus(userId);
        setStatus(newStatus);
        onStatusChange?.(newStatus);

        // Stop polling if workflow is complete
        if (newStatus.status !== "running") {
          setIsRunning(false);
        }
      } catch (err) {
        // Ignore errors during polling
        console.error("Status poll error:", err);
      }
    };

    // Initial poll
    pollStatus();

    // Poll every 2 seconds
    pollRef.current = setInterval(pollStatus, 2000);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [isRunning, userId, onStatusChange, setIsRunning]);

  const handleKill = async () => {
    if (!userId) return;

    setKilling(true);
    setError(null);

    try {
      await api.killWorkflow(userId);
      setIsRunning(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop workflow");
    } finally {
      setKilling(false);
    }
  };

  if (!isRunning && !status) {
    return null;
  }

  const progress = status
    ? (status.current_job_index / Math.max(status.total_jobs, 1)) * 100
    : 0;

  return (
    <Card>
      <CardHeader
        title="Workflow Status"
        description="Real-time status of autonomous job applications"
        action={
          isRunning && (
            <Button
              variant="danger"
              size="sm"
              onClick={handleKill}
              loading={killing}
            >
              🛑 Kill Switch
            </Button>
          )
        }
      />

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {status && (
        <div className="space-y-6">
          {/* Status Badge & Progress */}
          <div className="flex items-center justify-between">
            <StatusBadge status={status.status} />
            <span className="text-sm text-gray-500">
              {status.current_job_index} / {status.total_jobs} jobs processed
            </span>
          </div>

          <Progress value={progress} showLabel />

          {/* Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard
              label="Submitted"
              value={status.applications_submitted}
              variant="success"
            />
            <StatCard
              label="Failed"
              value={status.applications_failed}
              variant="error"
            />
            <StatCard
              label="Total Jobs"
              value={status.total_jobs}
              variant="default"
            />
            <StatCard
              label="Remaining"
              value={Math.max(0, status.total_jobs - status.current_job_index)}
              variant="info"
            />
          </div>

          {/* Logs */}
          {status.logs.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                Recent Logs
              </h4>
              <div className="bg-gray-900 rounded-lg p-4 max-h-48 overflow-y-auto font-mono text-xs">
                {status.logs.slice(-10).map((log, i) => (
                  <div key={i} className="text-green-400">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Errors */}
          {status.errors.length > 0 && (
            <div>
              <h4 className="font-medium text-red-600 dark:text-red-400 mb-2">
                Errors
              </h4>
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 max-h-32 overflow-y-auto">
                {status.errors.map((err, i) => (
                  <div
                    key={i}
                    className="text-sm text-red-600 dark:text-red-400"
                  >
                    {err}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  variant: "default" | "success" | "error" | "info";
}

function StatCard({ label, value, variant }: StatCardProps) {
  const colors = {
    default: "text-gray-900 dark:text-gray-100",
    success: "text-green-600 dark:text-green-400",
    error: "text-red-600 dark:text-red-400",
    info: "text-blue-600 dark:text-blue-400",
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
      <p className={`text-2xl font-bold ${colors[variant]}`}>{value}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{label}</p>
    </div>
  );
}
