"use client";

import { useState, useCallback } from "react";
import type { StudentProfile, ApplyPolicy } from "@/types";

const PROFILE_STORAGE_KEY = "job_agent_profile";
const POLICY_STORAGE_KEY = "job_agent_policy";

const DEFAULT_POLICY: ApplyPolicy = {
  max_applications_per_day: 50,
  min_match_threshold: 30,
  blocked_companies: [],
  blocked_role_types: [],
  require_remote: false,
  required_location: null,
  enabled: true,
};

export function useStudentProfile() {
  const [profile, setProfileState] = useState<StudentProfile | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const stored = localStorage.getItem(PROFILE_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const setProfile = useCallback((newProfile: StudentProfile | null) => {
    setProfileState(newProfile);
    if (newProfile) {
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(newProfile));
    } else {
      localStorage.removeItem(PROFILE_STORAGE_KEY);
    }
  }, []);

  const clearProfile = useCallback(() => {
    setProfileState(null);
    localStorage.removeItem(PROFILE_STORAGE_KEY);
  }, []);

  return { profile, setProfile, clearProfile };
}

export function useApplyPolicy() {
  const [policy, setPolicyState] = useState<ApplyPolicy>(() => {
    if (typeof window === "undefined") return DEFAULT_POLICY;
    try {
      const stored = localStorage.getItem(POLICY_STORAGE_KEY);
      return stored ? { ...DEFAULT_POLICY, ...JSON.parse(stored) } : DEFAULT_POLICY;
    } catch {
      return DEFAULT_POLICY;
    }
  });

  const setPolicy = useCallback((newPolicy: ApplyPolicy) => {
    setPolicyState(newPolicy);
    localStorage.setItem(POLICY_STORAGE_KEY, JSON.stringify(newPolicy));
  }, []);

  const resetPolicy = useCallback(() => {
    setPolicyState(DEFAULT_POLICY);
    localStorage.setItem(POLICY_STORAGE_KEY, JSON.stringify(DEFAULT_POLICY));
  }, []);

  return { policy, setPolicy, resetPolicy };
}
