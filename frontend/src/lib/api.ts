import type {
  StudentProfile,
  ApplyPolicy,
  WorkflowStatus,
  ApplicationRecord,
  ApplicationSummary,
  User,
  UserAuth,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth endpoints
  async signup(data: UserAuth): Promise<User> {
    return this.request<User>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async login(data: UserAuth): Promise<User> {
    return this.request<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Resume endpoints
  async uploadResume(file: File): Promise<{ success: boolean; profile: StudentProfile }> {
    const formData = new FormData();
    formData.append("file", file);

    const headers: HeadersInit = {};
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}/resume/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Workflow endpoints
  async startWorkflow(data: {
    user_id: string;
    student_profile: StudentProfile;
    bullet_bank: StudentProfile["bullet_bank"];
    answer_library: StudentProfile["answer_library"];
    proof_pack: StudentProfile["proof_pack"];
    apply_policy: ApplyPolicy;
  }): Promise<{ success: boolean; message: string; user_id: string }> {
    return this.request("/workflow/start", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getWorkflowStatus(userId: string): Promise<WorkflowStatus> {
    return this.request(`/workflow/status/${userId}`);
  }

  async killWorkflow(userId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/workflow/kill/${userId}`, {
      method: "POST",
    });
  }

  // Tracker endpoints
  async getApplications(
    userId: string,
    status?: string
  ): Promise<{
    user_id: string;
    summary: ApplicationSummary;
    applications: ApplicationRecord[];
  }> {
    const params = status ? `?status=${status}` : "";
    return this.request(`/tracker/applications/${userId}${params}`);
  }

  async getApplicationDetail(
    userId: string,
    jobId: string
  ): Promise<ApplicationRecord> {
    return this.request(`/tracker/applications/${userId}/${jobId}`);
  }

  async retryApplication(
    userId: string,
    jobId: string
  ): Promise<{ success: boolean; message: string }> {
    return this.request(`/tracker/applications/${userId}/${jobId}/retry`, {
      method: "POST",
    });
  }

  async clearApplications(userId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/tracker/applications/${userId}`, {
      method: "DELETE",
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; sandbox_url: string; version: string }> {
    return this.request("/");
  }

  // SSE stream URL for real-time workflow updates
  getWorkflowStreamUrl(userId: string): string {
    return `${API_BASE}/workflow/stream/${userId}`;
  }
}

export const api = new ApiService();
