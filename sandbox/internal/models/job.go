package models

// Job represents a job posting in the sandbox portal
type Job struct {
	ID                  string   `json:"id"`
	Title               string   `json:"title"`
	Company             string   `json:"company"`
	Description         string   `json:"description"`
	Requirements        []string `json:"requirements"`
	Location            string   `json:"location"`
	IsRemote            bool     `json:"is_remote"`
	Remote              bool     `json:"remote"` // Alias for is_remote
	Salary              string   `json:"salary,omitempty"`
	ExperienceRequired  int      `json:"experience_required"` // Years
	ExperienceYears     int      `json:"experience_years"`    // Alias
	JobType             string   `json:"job_type"`            // full-time, part-time, internship, contract
	PostedAt            string   `json:"posted_at"`
	ApplicationDeadline string   `json:"application_deadline,omitempty"`
	Benefits            []string `json:"benefits,omitempty"`
	CompanySize         string   `json:"company_size,omitempty"`
	Industry            string   `json:"industry,omitempty"`
	ApplicationURL      string   `json:"application_url,omitempty"`
}

// JobsResponse is the response for listing jobs
type JobsResponse struct {
	Jobs  []Job `json:"jobs"`
	Total int   `json:"total"`
	Limit int   `json:"limit"`
}

// JobDetailResponse is the response for a single job
type JobDetailResponse struct {
	Job               Job      `json:"job"`
	SimilarJobs       []string `json:"similar_jobs,omitempty"`
	ApplicationsCount int      `json:"applications_count"`
	IsAcceptingApps   bool     `json:"is_accepting_applications"`
}
