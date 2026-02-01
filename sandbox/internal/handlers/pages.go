package handlers

import (
	"embed"
	"html/template"
	"io/fs"
	"net/http"
	"strings"
	"time"

	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/store"
	"github.com/gin-gonic/gin"
)

// PageHandler handles frontend page rendering
type PageHandler struct {
	jobStore  *store.JobStore
	appStore  *store.ApplicationStore
	templates map[string]*template.Template
}

// TemplatesFS is the embedded filesystem for templates (set from main)
var TemplatesFS embed.FS

// NewPageHandler creates a new page handler
func NewPageHandler(jobStore *store.JobStore, appStore *store.ApplicationStore, templatesDir fs.FS) (*PageHandler, error) {
	// Define template functions
	funcMap := template.FuncMap{
		"slice": func(s string, start, end int) string {
			if len(s) == 0 {
				return ""
			}
			if start >= len(s) {
				return ""
			}
			if end > len(s) {
				end = len(s)
			}
			return s[start:end]
		},
		"minus": func(a, b int) int {
			return a - b
		},
		"add": func(a, b int) int {
			return a + b
		},
		"lower": strings.ToLower,
		"eq": func(a, b interface{}) bool {
			return a == b
		},
	}

	templates := make(map[string]*template.Template)

	// Parse each page template with base
	pageTemplates := []string{
		"jobs_list.html",
		"job_detail.html",
		"apply_form.html",
		"application_success.html",
		"my_applications.html",
		"application_detail.html",
	}

	baseContent, err := fs.ReadFile(templatesDir, "base.html")
	if err != nil {
		return nil, err
	}

	for _, page := range pageTemplates {
		pageContent, err := fs.ReadFile(templatesDir, page)
		if err != nil {
			return nil, err
		}

		// Combine base and page
		combined := string(baseContent) + "\n" + string(pageContent)
		tmpl, err := template.New(page).Funcs(funcMap).Parse(combined)
		if err != nil {
			return nil, err
		}
		templates[page] = tmpl
	}

	return &PageHandler{
		jobStore:  jobStore,
		appStore:  appStore,
		templates: templates,
	}, nil
}

// render renders a template
func (h *PageHandler) render(c *gin.Context, templateName string, data gin.H) {
	c.Header("Content-Type", "text/html; charset=utf-8")

	tmpl, ok := h.templates[templateName]
	if !ok {
		c.String(http.StatusInternalServerError, "Template not found: %s", templateName)
		return
	}

	err := tmpl.Execute(c.Writer, data)
	if err != nil {
		c.String(http.StatusInternalServerError, "Template error: %v", err)
		return
	}
}

// HomePage renders the job listing page
func (h *PageHandler) HomePage(c *gin.Context) {
	query := c.Query("q")
	remote := c.Query("remote")
	jobType := c.Query("type")
	limit := 100

	var jobs interface{}

	if query != "" {
		jobs = h.jobStore.Search(query, limit)
	} else if remote == "true" {
		jobs = h.jobStore.FilterByRemote(limit)
	} else if jobType != "" {
		jobs = h.jobStore.FilterByJobType(jobType, limit)
	} else {
		jobs = h.jobStore.GetAll(limit)
	}

	// Count unique companies
	companySet := make(map[string]bool)
	allJobs := h.jobStore.GetAll(0)
	for _, job := range allJobs {
		companySet[job.Company] = true
	}

	data := gin.H{
		"Title":           "Find Your Dream Job",
		"Jobs":            jobs,
		"TotalJobs":       h.jobStore.GetCount(),
		"Query":           query,
		"RemoteOnly":      remote == "true",
		"JobType":         jobType,
		"UniqueCompanies": len(companySet),
	}

	h.render(c, "jobs_list.html", data)
}

// JobDetailPage renders the job detail page
func (h *PageHandler) JobDetailPage(c *gin.Context) {
	jobID := c.Param("id")

	job, exists := h.jobStore.GetByID(jobID)
	if !exists {
		c.String(http.StatusNotFound, "Job not found")
		return
	}

	// Check if accepting applications
	isAccepting := true
	deadlineDate := ""
	if job.ApplicationDeadline != "" {
		deadline, err := time.Parse(time.RFC3339, job.ApplicationDeadline)
		if err == nil {
			deadlineDate = deadline.Format("January 2, 2006")
			if time.Now().After(deadline) {
				isAccepting = false
			}
		}
	}

	// Parse posted date
	postedDate := ""
	if job.PostedAt != "" {
		posted, err := time.Parse(time.RFC3339, job.PostedAt)
		if err == nil {
			postedDate = posted.Format("January 2, 2006")
		}
	}

	data := gin.H{
		"Title":             job.Title + " at " + job.Company,
		"Job":               job,
		"IsAccepting":       isAccepting,
		"ApplicationsCount": h.appStore.GetCountByJobID(jobID),
		"PostedDate":        postedDate,
		"DeadlineDate":      deadlineDate,
	}

	h.render(c, "job_detail.html", data)
}

// ApplyPage renders the application form
func (h *PageHandler) ApplyPage(c *gin.Context) {
	jobID := c.Param("id")

	job, exists := h.jobStore.GetByID(jobID)
	if !exists {
		c.String(http.StatusNotFound, "Job not found")
		return
	}

	// Check if accepting applications
	if job.ApplicationDeadline != "" {
		deadline, err := time.Parse(time.RFC3339, job.ApplicationDeadline)
		if err == nil && time.Now().After(deadline) {
			c.Redirect(http.StatusFound, "/jobs/"+jobID)
			return
		}
	}

	data := gin.H{
		"Title": "Apply for " + job.Title,
		"Job":   job,
	}

	h.render(c, "apply_form.html", data)
}

// ApplicationSuccessPage renders the success page after application submission
func (h *PageHandler) ApplicationSuccessPage(c *gin.Context) {
	confirmationID := c.Param("id")

	app, exists := h.appStore.GetByID(confirmationID)
	if !exists {
		c.Redirect(http.StatusFound, "/my-applications")
		return
	}

	data := gin.H{
		"Title":       "Application Submitted",
		"Application": app,
		"SubmittedAt": app.SubmittedAt.Format("January 2, 2006 at 3:04 PM"),
	}

	h.render(c, "application_success.html", data)
}

// MyApplicationsPage renders the list of applications
func (h *PageHandler) MyApplicationsPage(c *gin.Context) {
	email := c.Query("email")

	var apps interface{}

	if email != "" {
		apps = h.appStore.GetByEmail(email)
	} else {
		apps = h.appStore.GetAll(50)
	}

	data := gin.H{
		"Title":        "My Applications",
		"Applications": apps,
		"Email":        email,
	}

	h.render(c, "my_applications.html", data)
}

// ApplicationDetailPage renders the application detail page
func (h *PageHandler) ApplicationDetailPage(c *gin.Context) {
	confirmationID := c.Param("id")

	app, exists := h.appStore.GetByID(confirmationID)
	if !exists {
		c.String(http.StatusNotFound, "Application not found")
		return
	}

	data := gin.H{
		"Title":       "Application " + app.ConfirmationID,
		"Application": app,
		"SubmittedAt": app.SubmittedAt.Format("January 2, 2006 at 3:04 PM"),
		"UpdatedAt":   app.UpdatedAt.Format("January 2, 2006 at 3:04 PM"),
	}

	h.render(c, "application_detail.html", data)
}

// ApplicationLookup handles application lookup
func (h *PageHandler) ApplicationLookup(c *gin.Context) {
	id := c.Query("id")
	if id == "" {
		c.Redirect(http.StatusFound, "/my-applications")
		return
	}

	app, exists := h.appStore.GetByID(id)
	if !exists {
		c.Redirect(http.StatusFound, "/my-applications?error=not_found")
		return
	}

	c.Redirect(http.StatusFound, "/applications/"+app.ConfirmationID)
}
