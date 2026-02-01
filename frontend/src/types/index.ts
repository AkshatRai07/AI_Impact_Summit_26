// Types matching backend schemas

export interface Bullet {
  text: string;
  source: string;
  metrics?: string | null;
  skills_demonstrated: string[];
}

export interface ProofItem {
  title: string;
  url: string;
  description: string;
  related_to: string;
}

export interface ExperienceItem {
  company: string;
  role: string;
  duration: string;
  description: string;
  bullets: string[];
}

export interface ProjectItem {
  name: string;
  description: string;
  technologies: string[];
  url?: string | null;
  bullets: string[];
}

export interface EducationItem {
  institution: string;
  degree: string;
  field: string;
  graduation_date: string;
  gpa?: string | null;
}

export interface Constraints {
  locations: string[];
  remote_preference: "remote_only" | "hybrid" | "onsite" | "flexible";
  visa_required: boolean;
  work_authorization: string;
  earliest_start_date?: string | null;
  salary_expectation?: string | null;
}

export interface AnswerLibrary {
  work_authorization: string;
  availability: string;
  relocation: string;
  salary_expectations: string;
  why_interested: string;
  greatest_strength: string;
  custom_answers: Record<string, string>;
}

export interface StudentProfile {
  full_name: string;
  email: string;
  phone?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  education: EducationItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  skills: string[];
  bullet_bank: Bullet[];
  proof_pack: ProofItem[];
  answer_library: AnswerLibrary;
  constraints: Constraints;
  raw_text: string;
}

export interface JobPosting {
  id: string;
  title: string;
  company: string;
  description: string;
  requirements: string[];
  location: string;
  remote?: boolean | null;
  salary?: string | null;
}

export interface ApplyPolicy {
  max_applications_per_day: number;
  min_match_threshold: number;
  blocked_companies: string[];
  blocked_role_types: string[];
  require_remote: boolean;
  required_location?: string | null;
  enabled: boolean;
}

export interface ApplicationRecord {
  job_id: string;
  job_title: string;
  company: string;
  status: "queued" | "submitted" | "failed" | "retried";
  submitted_at?: string;
  confirmation_id?: string;
  error_message?: string;
  retry_count?: number;
  match_score?: number;
  match_reasoning?: string;
  evidence_mapping?: Array<{
    requirement: string;
    evidence: string;
  }>;
}

export interface WorkflowStatus {
  user_id: string;
  status: "running" | "completed" | "failed" | "stopped";
  applications_submitted: number;
  applications_failed: number;
  current_job_index: number;
  total_jobs: number;
  logs: string[];
  errors: string[];
}

export interface ApplicationSummary {
  total: number;
  submitted: number;
  failed: number;
  success_rate: number;
}

export interface UserAuth {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  access_token: string;
}
