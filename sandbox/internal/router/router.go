package router

import (
	"io/fs"
	"time"

	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/handlers"
	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/middleware"
	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/store"
	"github.com/gin-gonic/gin"
)

// Config holds router configuration
type Config struct {
	// EnableFailureSimulation enables random failure simulation for testing retries
	EnableFailureSimulation bool
	// FailureRate is the rate of failures (0.0 to 1.0)
	FailureRate float64
	// SlowdownRate is the rate of slowdowns (0.0 to 1.0)
	SlowdownRate float64
	// TimeoutRate is the rate of timeouts (0.0 to 1.0)
	TimeoutRate float64
	// GeneralRateLimit is the rate limit for general endpoints (requests per minute)
	GeneralRateLimit int
	// ApplicationRateLimit is the rate limit for application submissions (requests per minute)
	ApplicationRateLimit int
	// TemplatesFS is the filesystem for templates (optional, for frontend)
	TemplatesFS fs.FS
}

// DefaultConfig returns the default router configuration
func DefaultConfig() Config {
	return Config{
		EnableFailureSimulation: false,
		FailureRate:             0.05, // 5% failure rate
		SlowdownRate:            0.03, // 3% slowdown rate
		TimeoutRate:             0.02, // 2% timeout rate
		GeneralRateLimit:        100,  // 100 requests per minute
		ApplicationRateLimit:    30,   // 30 applications per minute
		TemplatesFS:             nil,
	}
}

// SetupRouter creates and configures the Gin router
func SetupRouter(config Config) *gin.Engine {
	// Create Gin router
	router := gin.New()

	// Initialize stores
	jobStore := store.NewJobStore()
	appStore := store.NewApplicationStore()

	// Initialize handlers
	jobHandler := handlers.NewJobHandler(jobStore, appStore)
	appHandler := handlers.NewApplicationHandler(jobStore, appStore)
	healthHandler := handlers.NewHealthHandler(jobStore, appStore)

	// Initialize rate limiters
	generalLimiter := middleware.NewRateLimiter(config.GeneralRateLimit, time.Minute)
	appLimiter := middleware.NewRateLimiter(config.ApplicationRateLimit, time.Minute)

	// Apply global middleware
	router.Use(gin.Recovery())
	router.Use(middleware.CORSMiddleware())
	router.Use(middleware.LoggerMiddleware())
	router.Use(middleware.ErrorHandlerMiddleware())
	router.Use(middleware.RequestIDMiddleware())
	router.Use(middleware.RateLimitMiddleware(generalLimiter))

	// Optionally enable failure simulation
	if config.EnableFailureSimulation {
		failureSimulator := middleware.NewFailureSimulator(
			config.FailureRate,
			config.SlowdownRate,
			config.TimeoutRate,
		)
		router.Use(middleware.FailureMiddleware(failureSimulator))
	}

	// Health endpoints (no rate limiting)
	router.GET("/health", healthHandler.HealthCheck)
	router.GET("/ready", healthHandler.ReadinessCheck)
	router.GET("/live", healthHandler.LivenessCheck)

	// API info endpoint
	router.GET("/api", healthHandler.GetAPIInfo)

	// API routes
	api := router.Group("/api")
	{
		// Jobs endpoints
		jobs := api.Group("/jobs")
		{
			jobs.GET("", jobHandler.ListJobs)
			jobs.GET("/search", jobHandler.SearchJobs)
			jobs.GET("/:id", jobHandler.GetJob)
			jobs.GET("/:id/requirements", jobHandler.GetJobRequirements)
		}

		// Companies endpoints
		api.GET("/companies/:company/jobs", jobHandler.GetJobsByCompany)

		// Applications endpoints (stricter rate limiting)
		applications := api.Group("/applications")
		{
			applications.POST("", middleware.ApplicationRateLimitMiddleware(appLimiter), appHandler.SubmitApplication)
			applications.GET("", appHandler.ListApplications)
			applications.GET("/:id", appHandler.GetApplication)
			applications.GET("/:id/receipt", appHandler.GetApplicationReceipt)
			applications.PATCH("/:id/status", appHandler.UpdateApplicationStatus)
			applications.DELETE("/clear", appHandler.ClearAllApplications)
		}

		// Stats endpoint
		api.GET("/stats", healthHandler.GetStats)
	}

	// Frontend page routes (if templates are provided)
	if config.TemplatesFS != nil {
		pageHandler, err := handlers.NewPageHandler(jobStore, appStore, config.TemplatesFS)
		if err != nil {
			panic("Failed to initialize page handler: " + err.Error())
		}

		// Home page (job listings)
		router.GET("/", pageHandler.HomePage)
		router.GET("/jobs", pageHandler.HomePage)

		// Job detail page
		router.GET("/jobs/:id", pageHandler.JobDetailPage)

		// Apply page
		router.GET("/jobs/:id/apply", pageHandler.ApplyPage)

		// Application routes
		router.GET("/applications", pageHandler.MyApplicationsPage)
		router.GET("/applications/:id", pageHandler.ApplicationDetailPage)
		router.GET("/applications/:id/success", pageHandler.ApplicationSuccessPage)
		router.GET("/my-applications", pageHandler.MyApplicationsPage)
		router.GET("/lookup", pageHandler.ApplicationLookup)
	}

	return router
}
