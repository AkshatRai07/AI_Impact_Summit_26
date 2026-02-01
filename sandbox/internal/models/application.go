package models

import "time"

// ApplicationStatus represents the current status of an application
type ApplicationStatus string

const (
	StatusReceived    ApplicationStatus = "received"
	StatusReviewing   ApplicationStatus = "reviewing"
	StatusSubmitted   ApplicationStatus = "submitted"
	StatusRejected    ApplicationStatus = "rejected"
	StatusShortlisted ApplicationStatus = "shortlisted"
)

// ApplicationRequest is the payload for submitting an application
type ApplicationRequest struct {
	JobID          string `json:"job_id" binding:"required"`
	ApplicantName  string `json:"applicant_name" binding:"required"`
	ApplicantEmail string `json:"applicant_email" binding:"required,email"`
	Resume         string `json:"resume" binding:"required"`
	CoverLetter    string `json:"cover_letter"`
	Phone          string `json:"phone,omitempty"`
	LinkedIn       string `json:"linkedin,omitempty"`
	Portfolio      string `json:"portfolio,omitempty"`
	GitHub         string `json:"github,omitempty"`

	// Additional common application fields
	WorkAuthorization string `json:"work_authorization,omitempty"`
	SponsorshipNeeded *bool  `json:"sponsorship_needed,omitempty"`
	StartDate         string `json:"start_date,omitempty"`
	Availability      string `json:"availability,omitempty"`
	SalaryExpectation string `json:"salary_expectation,omitempty"`
	RelocationWilling *bool  `json:"relocation_willing,omitempty"`
	RemotePreference  string `json:"remote_preference,omitempty"`

	// Custom answers for job-specific questions
	CustomAnswers map[string]string `json:"custom_answers,omitempty"`
}

// Application represents a stored application record
type Application struct {
	ID             string            `json:"id"`
	ConfirmationID string            `json:"confirmation_id"`
	ApplicationID  string            `json:"application_id"` // Alias
	JobID          string            `json:"job_id"`
	JobTitle       string            `json:"job_title"`
	Company        string            `json:"company"`
	ApplicantName  string            `json:"applicant_name"`
	ApplicantEmail string            `json:"applicant_email"`
	Resume         string            `json:"resume"`
	CoverLetter    string            `json:"cover_letter"`
	Status         ApplicationStatus `json:"status"`
	SubmittedAt    time.Time         `json:"submitted_at"`
	UpdatedAt      time.Time         `json:"updated_at"`
	ReviewedAt     *time.Time        `json:"reviewed_at,omitempty"`
	Notes          string            `json:"notes,omitempty"`

	// Additional fields
	Phone             string            `json:"phone,omitempty"`
	LinkedIn          string            `json:"linkedin,omitempty"`
	Portfolio         string            `json:"portfolio,omitempty"`
	GitHub            string            `json:"github,omitempty"`
	WorkAuthorization string            `json:"work_authorization,omitempty"`
	CustomAnswers     map[string]string `json:"custom_answers,omitempty"`
}

// ApplicationResponse is returned after a successful submission
type ApplicationResponse struct {
	Success        bool              `json:"success"`
	ConfirmationID string            `json:"confirmation_id"`
	ApplicationID  string            `json:"application_id"` // Alias for confirmation_id
	Status         ApplicationStatus `json:"status"`
	Message        string            `json:"message"`
	SubmittedAt    string            `json:"submitted_at"`
	JobID          string            `json:"job_id"`
	JobTitle       string            `json:"job_title"`
	Company        string            `json:"company"`
}

// ApplicationStatusResponse is returned when querying application status
type ApplicationStatusResponse struct {
	ApplicationID  string            `json:"application_id"`
	ConfirmationID string            `json:"confirmation_id"`
	JobID          string            `json:"job_id"`
	JobTitle       string            `json:"job_title"`
	Company        string            `json:"company"`
	Status         ApplicationStatus `json:"status"`
	SubmittedAt    string            `json:"submitted_at"`
	UpdatedAt      string            `json:"updated_at"`
	Message        string            `json:"message,omitempty"`
}

// ErrorResponse for API errors
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
	Code    int    `json:"code"`
}

// HealthResponse for health check endpoint
type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version"`
	Uptime    string `json:"uptime"`
}

// StatsResponse for sandbox statistics
type StatsResponse struct {
	TotalJobs            int            `json:"total_jobs"`
	TotalApplications    int            `json:"total_applications"`
	ApplicationsByStatus map[string]int `json:"applications_by_status"`
	TopCompanies         []string       `json:"top_companies"`
}
