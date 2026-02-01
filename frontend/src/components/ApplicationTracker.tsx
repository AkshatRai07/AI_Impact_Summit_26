"use client";

import { useEffect, useState } from "react";
import type { ApplicationRecord, ApplicationSummary } from "@/types";
import { Card, CardHeader, Button, StatusBadge, Badge } from "@/components/ui";
import { api } from "@/lib/api";

interface ApplicationTrackerProps {
  userId: string;
  refreshTrigger?: number;
}

export function ApplicationTracker({
  userId,
  refreshTrigger,
}: ApplicationTrackerProps) {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [retrying, setRetrying] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;

    const fetchApplications = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await api.getApplications(userId, filter);
        setApplications(data.applications);
        setSummary(data.summary);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch applications");
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, [userId, filter, refreshTrigger]);

  const handleRetry = async (jobId: string) => {
    setRetrying(jobId);

    try {
      await api.retryApplication(userId, jobId);
      // Refresh the list
      const data = await api.getApplications(userId, filter);
      setApplications(data.applications);
      setSummary(data.summary);
    } catch (err) {
      console.error("Retry failed:", err);
    } finally {
      setRetrying(null);
    }
  };

  const filters = [
    { value: undefined, label: "All" },
    { value: "submitted", label: "Submitted" },
    { value: "failed", label: "Failed" },
    { value: "queued", label: "Queued" },
  ];

  return (
    <Card>
      <CardHeader
        title="Application Tracker"
        description="Track all your submitted applications"
      />

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {summary.total}
            </p>
            <p className="text-xs text-gray-500">Total</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {summary.submitted}
            </p>
            <p className="text-xs text-gray-500">Submitted</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">{summary.failed}</p>
            <p className="text-xs text-gray-500">Failed</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {summary.success_rate}%
            </p>
            <p className="text-xs text-gray-500">Success Rate</p>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-4 border-b border-gray-200 dark:border-gray-700 pb-4">
        {filters.map((f) => (
          <button
            key={f.label}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filter === f.value
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto" />
          <p className="text-sm text-gray-500 mt-2">Loading applications...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && applications.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No applications found.
        </div>
      )}

      {/* Applications List */}
      {!loading && applications.length > 0 && (
        <div className="space-y-3">
          {applications.map((app) => (
            <div
              key={app.job_id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              {/* Header Row */}
              <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                onClick={() =>
                  setExpandedId(expandedId === app.job_id ? null : app.job_id)
                }
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {app.job_title}
                    </h4>
                    <StatusBadge status={app.status} />
                  </div>
                  <p className="text-sm text-gray-500 truncate">{app.company}</p>
                </div>

                <div className="flex items-center gap-3">
                  {app.match_score && (
                    <Badge
                      variant={app.match_score >= 70 ? "success" : "default"}
                      size="sm"
                    >
                      {Math.round(app.match_score)}% match
                    </Badge>
                  )}
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform ${
                      expandedId === app.job_id ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedId === app.job_id && (
                <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4 bg-gray-50 dark:bg-gray-800/50">
                  <div className="space-y-3 text-sm">
                    {app.submitted_at && (
                      <p>
                        <span className="text-gray-500">Submitted:</span>{" "}
                        {new Date(app.submitted_at).toLocaleString()}
                      </p>
                    )}

                    {app.confirmation_id && (
                      <p>
                        <span className="text-gray-500">Confirmation ID:</span>{" "}
                        <code className="bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded">
                          {app.confirmation_id}
                        </code>
                      </p>
                    )}

                    {app.match_reasoning && (
                      <p>
                        <span className="text-gray-500">Match Reasoning:</span>{" "}
                        {app.match_reasoning}
                      </p>
                    )}

                    {app.error_message && (
                      <p className="text-red-600 dark:text-red-400">
                        <span className="text-gray-500">Error:</span>{" "}
                        {app.error_message}
                      </p>
                    )}

                    {app.evidence_mapping && app.evidence_mapping.length > 0 && (
                      <div>
                        <p className="text-gray-500 mb-2">Evidence Mapping:</p>
                        <div className="space-y-2">
                          {app.evidence_mapping.map((mapping, i) => (
                            <div
                              key={i}
                              className="p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
                            >
                              <p className="font-medium text-gray-700 dark:text-gray-300">
                                {mapping.requirement}
                              </p>
                              <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">
                                → {mapping.evidence}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Retry Button for Failed */}
                    {app.status === "failed" && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRetry(app.job_id);
                        }}
                        loading={retrying === app.job_id}
                      >
                        Retry Application
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
