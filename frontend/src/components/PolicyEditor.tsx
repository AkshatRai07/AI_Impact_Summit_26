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
    <Card glow>
      <CardHeader
        title="Apply Policy"
        description="Set constraints for autonomous job applications"
        action={
          <label className="flex items-center gap-3 cursor-pointer">
            <span className="text-sm text-slate-400">
              Enabled
            </span>
            <div className="relative">
              <input
                type="checkbox"
                checked={policy.enabled}
                onChange={(e) => updatePolicy({ enabled: e.target.checked })}
                disabled={disabled}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-700 peer-focus:ring-2 peer-focus:ring-blue-500/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-purple-500"></div>
            </div>
          </label>
        }
      />

      <div className="space-y-6">
        {/* Application Limits */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
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
              className="w-full px-4 py-3 rounded-xl
                bg-black/40 
                border border-white/10 
                text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50
                disabled:opacity-50 transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
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
              className="w-full px-4 py-3 rounded-xl
                bg-black/40 
                border border-white/10 
                text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50
                disabled:opacity-50 transition-all"
            />
          </div>
        </div>

        {/* Location Preferences */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
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
            <label className="flex items-center gap-3 cursor-pointer pb-3">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={policy.require_remote}
                  onChange={(e) =>
                    updatePolicy({ require_remote: e.target.checked })
                  }
                  disabled={disabled}
                  className="sr-only peer"
                />
                <div className="w-5 h-5 bg-slate-700 border border-white/10 rounded peer-focus:ring-2 peer-focus:ring-blue-500/50 peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-purple-500 peer-checked:border-transparent transition-all"></div>
                <svg className="absolute top-0.5 left-0.5 w-4 h-4 text-white hidden peer-checked:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-sm text-slate-300">
                Remote jobs only
              </span>
            </label>
          </div>
        </div>
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Remote jobs only
              </span>
          </div>

        {/* Blocked Companies */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Blocked Companies
          </label>
          <div className="flex gap-2 mb-3">
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
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-400 rounded-full text-sm"
                >
                  {company}
                  <button
                    onClick={() => removeBlockedCompany(i)}
                    disabled={disabled}
                    className="hover:text-red-300 disabled:opacity-50 transition-colors"
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
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Blocked Role Types
          </label>
          <div className="flex gap-2 mb-3">
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
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-400 rounded-full text-sm"
                >
                  {role}
                  <button
                    onClick={() => removeBlockedRole(i)}
                    disabled={disabled}
                    className="hover:text-red-300 disabled:opacity-50 transition-colors"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
    </Card>
  );
}
