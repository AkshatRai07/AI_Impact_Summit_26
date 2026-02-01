"use client";

import { useState } from "react";
import type { ApplyPolicy } from "@/types";
import { Card, CardHeader, Button, Input } from "@/components/ui";

interface PolicyEditorProps {
  policy: ApplyPolicy;
  onChange: (policy: ApplyPolicy) => void;
  disabled?: boolean;
}

export function PolicyEditor({ policy, onChange, disabled }: PolicyEditorProps) {
  const [blockedCompany, setBlockedCompany] = useState("");
  const [blockedRole, setBlockedRole] = useState("");

  const updatePolicy = (updates: Partial<ApplyPolicy>) => {
    onChange({ ...policy, ...updates });
  };

  const addBlockedCompany = () => {
    if (blockedCompany.trim()) {
      updatePolicy({
        blocked_companies: [...policy.blocked_companies, blockedCompany.trim()],
      });
      setBlockedCompany("");
    }
  };

  const removeBlockedCompany = (index: number) => {
    updatePolicy({
      blocked_companies: policy.blocked_companies.filter((_, i) => i !== index),
    });
  };

  const addBlockedRole = () => {
    if (blockedRole.trim()) {
      updatePolicy({
        blocked_role_types: [...policy.blocked_role_types, blockedRole.trim()],
      });
      setBlockedRole("");
    }
  };

  const removeBlockedRole = (index: number) => {
    updatePolicy({
      blocked_role_types: policy.blocked_role_types.filter((_, i) => i !== index),
    });
  };

  return (
    <Card>
      <CardHeader
        title="Apply Policy"
        description="Set constraints for autonomous job applications"
        action={
          <label className="flex items-center gap-2 cursor-pointer">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Enabled
            </span>
            <input
              type="checkbox"
              checked={policy.enabled}
              onChange={(e) => updatePolicy({ enabled: e.target.checked })}
              disabled={disabled}
              className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </label>
        }
      />

      <div className="space-y-6">
        {/* Application Limits */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Max Applications per Day
            </label>
            <input
              type="number"
              min={1}
              max={100}
              value={policy.max_applications_per_day}
              onChange={(e) =>
                updatePolicy({
                  max_applications_per_day: parseInt(e.target.value) || 50,
                })
              }
              disabled={disabled}
              className="w-full px-3 py-2 border rounded-lg shadow-sm 
                bg-white dark:bg-gray-900 
                border-gray-300 dark:border-gray-700 
                text-gray-900 dark:text-gray-100
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Minimum Match Threshold (%)
            </label>
            <input
              type="number"
              min={0}
              max={100}
              value={policy.min_match_threshold}
              onChange={(e) =>
                updatePolicy({
                  min_match_threshold: parseFloat(e.target.value) || 30,
                })
              }
              disabled={disabled}
              className="w-full px-3 py-2 border rounded-lg shadow-sm 
                bg-white dark:bg-gray-900 
                border-gray-300 dark:border-gray-700 
                text-gray-900 dark:text-gray-100
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                disabled:opacity-50"
            />
          </div>
        </div>

        {/* Location Preferences */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Required Location (optional)
            </label>
            <Input
              placeholder="e.g., San Francisco, CA"
              value={policy.required_location || ""}
              onChange={(e) =>
                updatePolicy({ required_location: e.target.value || null })
              }
              disabled={disabled}
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer pb-2">
              <input
                type="checkbox"
                checked={policy.require_remote}
                onChange={(e) =>
                  updatePolicy({ require_remote: e.target.checked })
                }
                disabled={disabled}
                className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Remote jobs only
              </span>
            </label>
          </div>
        </div>

        {/* Blocked Companies */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Blocked Companies
          </label>
          <div className="flex gap-2 mb-2">
            <Input
              placeholder="Company name"
              value={blockedCompany}
              onChange={(e) => setBlockedCompany(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addBlockedCompany()}
              disabled={disabled}
            />
            <Button
              variant="secondary"
              onClick={addBlockedCompany}
              disabled={disabled || !blockedCompany.trim()}
            >
              Add
            </Button>
          </div>
          {policy.blocked_companies.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {policy.blocked_companies.map((company, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded-full text-sm"
                >
                  {company}
                  <button
                    onClick={() => removeBlockedCompany(i)}
                    disabled={disabled}
                    className="hover:text-red-600 disabled:opacity-50"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Blocked Role Types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Blocked Role Types
          </label>
          <div className="flex gap-2 mb-2">
            <Input
              placeholder="e.g., Intern, Manager"
              value={blockedRole}
              onChange={(e) => setBlockedRole(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addBlockedRole()}
              disabled={disabled}
            />
            <Button
              variant="secondary"
              onClick={addBlockedRole}
              disabled={disabled || !blockedRole.trim()}
            >
              Add
            </Button>
          </div>
          {policy.blocked_role_types.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {policy.blocked_role_types.map((role, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded-full text-sm"
                >
                  {role}
                  <button
                    onClick={() => removeBlockedRole(i)}
                    disabled={disabled}
                    className="hover:text-red-600 disabled:opacity-50"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
