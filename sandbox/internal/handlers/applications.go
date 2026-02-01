package handlers

import (
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/models"
	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/store"
	"github.com/gin-gonic/gin"
)

// ApplicationHandler handles application-related API endpoints
type ApplicationHandler struct {
	jobStore *store.JobStore
	appStore *store.ApplicationStore
}

// NewApplicationHandler creates a new application handler
func NewApplicationHandler(jobStore *store.JobStore, appStore *store.ApplicationStore) *ApplicationHandler {
	return &ApplicationHandler{
		jobStore: jobStore,
		appStore: appStore,
	}
}

// SubmitApplication handles POST /api/applications
// This is the main endpoint for submitting job applications
func (h *ApplicationHandler) SubmitApplication(c *gin.Context) {
	var req models.ApplicationRequest

	// Parse request body
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: "Invalid request body: " + err.Error(),
			Code:    400,
		})
		return
	}

	// Validate required fields
	if req.JobID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_job_id",
			Message: "Job ID is required.",
			Code:    400,
		})
		return
	}

	if req.ApplicantName == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_applicant_name",
			Message: "Applicant name is required.",
			Code:    400,
		})
		return
	}

	if req.ApplicantEmail == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_applicant_email",
			Message: "Applicant email is required.",
			Code:    400,
		})
		return
	}

	// Validate email format
	if !isValidEmail(req.ApplicantEmail) {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_email",
			Message: "Please provide a valid email address.",
			Code:    400,
		})
		return
	}

	if req.Resume == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_resume",
			Message: "Resume is required.",
			Code:    400,
		})
		return
	}

	// Check if job exists
	job, exists := h.jobStore.GetByID(req.JobID)
	if !exists {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "job_not_found",
			Message: "The specified job does not exist.",
			Code:    404,
		})
		return
	}

	// Check if job is still accepting applications
	if job.ApplicationDeadline != "" {
		deadline, err := time.Parse(time.RFC3339, job.ApplicationDeadline)
		if err == nil && time.Now().After(deadline) {
			c.JSON(http.StatusBadRequest, models.ErrorResponse{
				Error:   "deadline_passed",
				Message: "The application deadline for this job has passed.",
				Code:    400,
			})
			return
		}
	}

	// Create application
	app, err := h.appStore.Create(req, job)
	if err != nil {
		// Check if it's a duplicate application
		if strings.Contains(err.Error(), "duplicate") {
			c.JSON(http.StatusConflict, models.ErrorResponse{
				Error:   "duplicate_application",
				Message: "You have already applied to this job.",
				Code:    409,
			})
			return
		}

		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "application_failed",
			Message: "Failed to submit application: " + err.Error(),
			Code:    500,
		})
		return
	}

	// Return success response
	c.JSON(http.StatusCreated, models.ApplicationResponse{
		Success:        true,
		ConfirmationID: app.ConfirmationID,
		ApplicationID:  app.ConfirmationID, // Alias
		Status:         app.Status,
		Message:        "Application submitted successfully. You will receive a confirmation email shortly.",
		SubmittedAt:    app.SubmittedAt.Format(time.RFC3339),
		JobID:          app.JobID,
		JobTitle:       app.JobTitle,
		Company:        app.Company,
	})
}

// GetApplication handles GET /api/applications/:id
// Returns the status and details of an application
func (h *ApplicationHandler) GetApplication(c *gin.Context) {
	appID := c.Param("id")

	app, exists := h.appStore.GetByID(appID)
	if !exists {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "application_not_found",
			Message: "The specified application could not be found.",
			Code:    404,
		})
		return
	}

	c.JSON(http.StatusOK, models.ApplicationStatusResponse{
		ApplicationID:  app.ConfirmationID,
		ConfirmationID: app.ConfirmationID,
		JobID:          app.JobID,
		JobTitle:       app.JobTitle,
		Company:        app.Company,
		Status:         app.Status,
		SubmittedAt:    app.SubmittedAt.Format(time.RFC3339),
		UpdatedAt:      app.UpdatedAt.Format(time.RFC3339),
		Message:        getStatusMessage(app.Status),
	})
}

// ListApplications handles GET /api/applications
// Returns a list of applications (optionally filtered by email)
func (h *ApplicationHandler) ListApplications(c *gin.Context) {
	email := c.Query("email")
	jobID := c.Query("job_id")
	limitStr := c.DefaultQuery("limit", "100")
	limit, _ := strconv.Atoi(limitStr)

	var apps []*models.Application

	if email != "" {
		apps = h.appStore.GetByEmail(email)
	} else if jobID != "" {
		apps = h.appStore.GetByJobID(jobID)
	} else {
		apps = h.appStore.GetAll(limit)
	}

	// Convert to response format
	responses := make([]models.ApplicationStatusResponse, 0, len(apps))
	for _, app := range apps {
		responses = append(responses, models.ApplicationStatusResponse{
			ApplicationID:  app.ConfirmationID,
			ConfirmationID: app.ConfirmationID,
			JobID:          app.JobID,
			JobTitle:       app.JobTitle,
			Company:        app.Company,
			Status:         app.Status,
			SubmittedAt:    app.SubmittedAt.Format(time.RFC3339),
			UpdatedAt:      app.UpdatedAt.Format(time.RFC3339),
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"applications": responses,
		"total":        len(responses),
	})
}

// UpdateApplicationStatus handles PATCH /api/applications/:id/status
// Updates the status of an application (for testing/demo purposes)
func (h *ApplicationHandler) UpdateApplicationStatus(c *gin.Context) {
	appID := c.Param("id")

	var req struct {
		Status string `json:"status" binding:"required"`
		Notes  string `json:"notes"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: "Invalid request body: " + err.Error(),
			Code:    400,
		})
		return
	}

	// Validate status
	validStatuses := map[string]models.ApplicationStatus{
		"received":    models.StatusReceived,
		"reviewing":   models.StatusReviewing,
		"submitted":   models.StatusSubmitted,
		"rejected":    models.StatusRejected,
		"shortlisted": models.StatusShortlisted,
	}

	status, valid := validStatuses[req.Status]
	if !valid {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_status",
			Message: "Invalid status. Valid values: received, reviewing, submitted, rejected, shortlisted",
			Code:    400,
		})
		return
	}

	err := h.appStore.UpdateStatus(appID, status, req.Notes)
	if err != nil {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "application_not_found",
			Message: "The specified application could not be found.",
			Code:    404,
		})
		return
	}

	app, _ := h.appStore.GetByID(appID)

	c.JSON(http.StatusOK, gin.H{
		"success":        true,
		"application_id": app.ConfirmationID,
		"status":         app.Status,
		"message":        "Application status updated successfully.",
	})
}

// GetApplicationReceipt handles GET /api/applications/:id/receipt
// Returns a receipt/confirmation for the application
func (h *ApplicationHandler) GetApplicationReceipt(c *gin.Context) {
	appID := c.Param("id")

	app, exists := h.appStore.GetByID(appID)
	if !exists {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "application_not_found",
			Message: "The specified application could not be found.",
			Code:    404,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"receipt": gin.H{
			"confirmation_id":   app.ConfirmationID,
			"application_id":    app.ConfirmationID,
			"job_id":            app.JobID,
			"job_title":         app.JobTitle,
			"company":           app.Company,
			"applicant_name":    app.ApplicantName,
			"applicant_email":   app.ApplicantEmail,
			"submitted_at":      app.SubmittedAt.Format(time.RFC3339),
			"status":            app.Status,
			"receipt_generated": time.Now().Format(time.RFC3339),
		},
		"message": "This is your official application receipt. Please save this for your records.",
	})
}

// Helper functions

func isValidEmail(email string) bool {
	// Simple email validation
	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	return emailRegex.MatchString(email)
}

func getStatusMessage(status models.ApplicationStatus) string {
	messages := map[models.ApplicationStatus]string{
		models.StatusReceived:    "Your application has been received and is in our system.",
		models.StatusReviewing:   "Your application is currently being reviewed by our team.",
		models.StatusSubmitted:   "Your application has been submitted successfully.",
		models.StatusRejected:    "Unfortunately, we have decided not to move forward with your application at this time.",
		models.StatusShortlisted: "Congratulations! You have been shortlisted for the next round.",
	}

	if msg, ok := messages[status]; ok {
		return msg
	}
	return "Application status: " + string(status)
}
