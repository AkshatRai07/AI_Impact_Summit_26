package handlers

import (
	"net/http"
	"time"

	"github.com/AkshatRai07/ImpactSummitPrivate/internal/models"
	"github.com/AkshatRai07/ImpactSummitPrivate/internal/store"
	"github.com/gin-gonic/gin"
)

// Version is the current API version
const Version = "1.0.0"

// StartTime is when the server started
var StartTime time.Time

func init() {
	StartTime = time.Now()
}

// HealthHandler handles health-related endpoints
type HealthHandler struct {
	jobStore *store.JobStore
	appStore *store.ApplicationStore
}

// NewHealthHandler creates a new health handler
func NewHealthHandler(jobStore *store.JobStore, appStore *store.ApplicationStore) *HealthHandler {
	return &HealthHandler{
		jobStore: jobStore,
		appStore: appStore,
	}
}

// HealthCheck handles GET /health
// Returns the health status of the sandbox
func (h *HealthHandler) HealthCheck(c *gin.Context) {
	uptime := time.Since(StartTime)

	c.JSON(http.StatusOK, models.HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Format(time.RFC3339),
		Version:   Version,
		Uptime:    uptime.String(),
	})
}

// ReadinessCheck handles GET /ready
// Returns whether the service is ready to accept traffic
func (h *HealthHandler) ReadinessCheck(c *gin.Context) {
	// Check if stores are initialized
	jobCount := h.jobStore.GetCount()

	if jobCount == 0 {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status":  "not_ready",
			"message": "Job store not initialized",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":    "ready",
		"jobs":      jobCount,
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// LivenessCheck handles GET /live
// Returns whether the service is alive
func (h *HealthHandler) LivenessCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "alive",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

// GetStats handles GET /api/stats
// Returns statistics about the sandbox
func (h *HealthHandler) GetStats(c *gin.Context) {
	jobCount := h.jobStore.GetCount()
	appCount := h.appStore.GetCount()
	appStats := h.appStore.GetStats()

	// Get unique companies
	jobs := h.jobStore.GetAll(0)
	companySet := make(map[string]bool)
	for _, job := range jobs {
		companySet[job.Company] = true
	}
	companies := make([]string, 0, len(companySet))
	for company := range companySet {
		companies = append(companies, company)
	}

	// Sort by most common (just take first 10)
	if len(companies) > 10 {
		companies = companies[:10]
	}

	c.JSON(http.StatusOK, models.StatsResponse{
		TotalJobs:            jobCount,
		TotalApplications:    appCount,
		ApplicationsByStatus: appStats,
		TopCompanies:         companies,
	})
}

// GetAPIInfo handles GET /api
// Returns information about the API
func (h *HealthHandler) GetAPIInfo(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"name":        "Job Portal Sandbox API",
		"version":     Version,
		"description": "A sandbox job portal for testing autonomous job application agents",
		"endpoints": gin.H{
			"jobs": gin.H{
				"list":         "GET /api/jobs",
				"get":          "GET /api/jobs/:id",
				"search":       "GET /api/jobs/search?q=<query>",
				"requirements": "GET /api/jobs/:id/requirements",
			},
			"applications": gin.H{
				"submit":  "POST /api/applications",
				"get":     "GET /api/applications/:id",
				"list":    "GET /api/applications",
				"receipt": "GET /api/applications/:id/receipt",
				"status":  "PATCH /api/applications/:id/status",
			},
			"health": gin.H{
				"health": "GET /health",
				"ready":  "GET /ready",
				"live":   "GET /live",
			},
			"stats": "GET /api/stats",
		},
		"rate_limits": gin.H{
			"general":      "100 requests per minute",
			"applications": "30 requests per minute",
		},
		"uptime":    time.Since(StartTime).String(),
		"timestamp": time.Now().Format(time.RFC3339),
	})
}
