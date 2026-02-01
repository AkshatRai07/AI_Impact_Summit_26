package handlers

import (
	"net/http"
	"strconv"
	"time"

	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/models"
	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/store"
	"github.com/gin-gonic/gin"
)

// JobHandler handles job-related API endpoints
type JobHandler struct {
	jobStore *store.JobStore
	appStore *store.ApplicationStore
}

// NewJobHandler creates a new job handler
func NewJobHandler(jobStore *store.JobStore, appStore *store.ApplicationStore) *JobHandler {
	return &JobHandler{
		jobStore: jobStore,
		appStore: appStore,
	}
}

// ListJobs handles GET /api/jobs
// Returns a list of all available jobs with optional filtering
func (h *JobHandler) ListJobs(c *gin.Context) {
	// Parse query parameters
	limitStr := c.DefaultQuery("limit", "100")
	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit < 0 {
		limit = 100
	}

	query := c.Query("q")
	remote := c.Query("remote")
	jobType := c.Query("type")

	var jobs []models.Job

	// Apply filters
	if query != "" {
		jobs = h.jobStore.Search(query, limit)
	} else if remote == "true" {
		jobs = h.jobStore.FilterByRemote(limit)
	} else if jobType != "" {
		jobs = h.jobStore.FilterByJobType(jobType, limit)
	} else {
		jobs = h.jobStore.GetAll(limit)
	}

	// Return response in format expected by backend
	c.JSON(http.StatusOK, models.JobsResponse{
		Jobs:  jobs,
		Total: h.jobStore.GetCount(),
		Limit: limit,
	})
}

// GetJob handles GET /api/jobs/:id
// Returns detailed information about a specific job
func (h *JobHandler) GetJob(c *gin.Context) {
	jobID := c.Param("id")

	job, exists := h.jobStore.GetByID(jobID)
	if !exists {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "job_not_found",
			Message: "The requested job could not be found.",
			Code:    404,
		})
		return
	}

	// Get application count for this job
	appCount := h.appStore.GetCountByJobID(jobID)

	// Check if job is still accepting applications
	isAccepting := true
	if job.ApplicationDeadline != "" {
		deadline, err := time.Parse(time.RFC3339, job.ApplicationDeadline)
		if err == nil && time.Now().After(deadline) {
			isAccepting = false
		}
	}

	c.JSON(http.StatusOK, models.JobDetailResponse{
		Job:               job,
		ApplicationsCount: appCount,
		IsAcceptingApps:   isAccepting,
	})
}

// SearchJobs handles GET /api/jobs/search
// Performs a search across jobs
func (h *JobHandler) SearchJobs(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_query",
			Message: "Search query 'q' is required.",
			Code:    400,
		})
		return
	}

	limitStr := c.DefaultQuery("limit", "50")
	limit, _ := strconv.Atoi(limitStr)
	if limit <= 0 {
		limit = 50
	}

	jobs := h.jobStore.Search(query, limit)

	c.JSON(http.StatusOK, gin.H{
		"jobs":  jobs,
		"total": len(jobs),
		"query": query,
	})
}

// GetJobRequirements handles GET /api/jobs/:id/requirements
// Returns just the requirements for a job (useful for evidence mapping)
func (h *JobHandler) GetJobRequirements(c *gin.Context) {
	jobID := c.Param("id")

	job, exists := h.jobStore.GetByID(jobID)
	if !exists {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "job_not_found",
			Message: "The requested job could not be found.",
			Code:    404,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"job_id":       job.ID,
		"title":        job.Title,
		"company":      job.Company,
		"requirements": job.Requirements,
	})
}

// GetJobsByCompany handles GET /api/companies/:company/jobs
// Returns all jobs from a specific company
func (h *JobHandler) GetJobsByCompany(c *gin.Context) {
	company := c.Param("company")

	limitStr := c.DefaultQuery("limit", "50")
	limit, _ := strconv.Atoi(limitStr)

	jobs := h.jobStore.Search(company, limit)

	// Filter to only include jobs from this company
	filtered := make([]models.Job, 0)
	for _, job := range jobs {
		if containsIgnoreCase(job.Company, company) {
			filtered = append(filtered, job)
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"company": company,
		"jobs":    filtered,
		"total":   len(filtered),
	})
}

// containsIgnoreCase helper function
func containsIgnoreCase(s, substr string) bool {
	return len(s) >= len(substr) &&
		contains(toLower(s), toLower(substr))
}

func toLower(s string) string {
	result := make([]byte, len(s))
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c >= 'A' && c <= 'Z' {
			result[i] = c + 32
		} else {
			result[i] = c
		}
	}
	return string(result)
}

func contains(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
