package main

import (
	"embed"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"os"

	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/router"
)

//go:embed internal/templates/*.html
var templatesFS embed.FS

func main() {
	// Parse command line flags
	port := flag.Int("port", 8080, "Port to run the server on")
	enableFailures := flag.Bool("failures", false, "Enable failure simulation for testing")
	failureRate := flag.Float64("failure-rate", 0.05, "Failure rate (0.0 to 1.0)")
	slowdownRate := flag.Float64("slowdown-rate", 0.03, "Slowdown rate (0.0 to 1.0)")
	timeoutRate := flag.Float64("timeout-rate", 0.02, "Timeout rate (0.0 to 1.0)")
	generalLimit := flag.Int("rate-limit", 100, "General rate limit (requests per minute)")
	appLimit := flag.Int("app-rate-limit", 30, "Application rate limit (requests per minute)")
	noFrontend := flag.Bool("no-frontend", false, "Disable frontend (API only mode)")
	flag.Parse()

	// Check for environment variable override
	if envPort := os.Getenv("PORT"); envPort != "" {
		fmt.Sscanf(envPort, "%d", port)
	}

	// Get templates sub-filesystem
	var templatesFSSub fs.FS
	if !*noFrontend {
		var err error
		templatesFSSub, err = fs.Sub(templatesFS, "internal/templates")
		if err != nil {
			log.Printf("⚠️  Warning: Failed to load templates, running in API-only mode: %v", err)
			templatesFSSub = nil
		}
	}

	// Configure router
	config := router.Config{
		EnableFailureSimulation: *enableFailures,
		FailureRate:             *failureRate,
		SlowdownRate:            *slowdownRate,
		TimeoutRate:             *timeoutRate,
		GeneralRateLimit:        *generalLimit,
		ApplicationRateLimit:    *appLimit,
		TemplatesFS:             templatesFSSub,
	}

	// Setup and run router
	r := router.SetupRouter(config)

	// Print startup banner
	printBanner(*port, config)

	// Start server
	addr := fmt.Sprintf(":%d", *port)
	log.Printf("🚀 Job Portal Sandbox is running on http://localhost%s", addr)
	if config.TemplatesFS != nil {
		log.Printf("🌐 Frontend available at http://localhost%s/", addr)
	}
	log.Printf("📋 API documentation available at http://localhost%s/api", addr)

	if err := r.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func printBanner(port int, config router.Config) {
	banner := `
╔═══════════════════════════════════════════════════════════════╗
║                   JOB PORTAL SANDBOX                          ║
║              Autonomous Application Testing                   ║
╠═══════════════════════════════════════════════════════════════╣
║  This sandbox simulates a real job portal for testing         ║
║  autonomous job search and auto-apply agents.                 ║
╠═══════════════════════════════════════════════════════════════╣
║  Frontend:                                                    ║
║    GET  /                    - Job listings                   ║
║    GET  /jobs/:id            - Job details                    ║
║    GET  /jobs/:id/apply      - Application form               ║
║    GET  /applications/:id    - Application status             ║
╠═══════════════════════════════════════════════════════════════╣
║  API Endpoints:                                               ║
║    GET  /health              - Health check                   ║
║    GET  /api/jobs            - List all jobs                  ║
║    GET  /api/jobs/:id        - Get job details                ║
║    POST /api/applications    - Submit application             ║
║    GET  /api/applications/:id - Get application status        ║
║    GET  /api/stats           - Get sandbox statistics         ║
╚═══════════════════════════════════════════════════════════════╝
`
	fmt.Println(banner)

	fmt.Printf("Configuration:\n")
	fmt.Printf("  • Port: %d\n", port)
	fmt.Printf("  • Frontend: %v\n", config.TemplatesFS != nil)
	fmt.Printf("  • Failure Simulation: %v\n", config.EnableFailureSimulation)
	if config.EnableFailureSimulation {
		fmt.Printf("    - Failure Rate: %.1f%%\n", config.FailureRate*100)
		fmt.Printf("    - Slowdown Rate: %.1f%%\n", config.SlowdownRate*100)
		fmt.Printf("    - Timeout Rate: %.1f%%\n", config.TimeoutRate*100)
	}
	fmt.Printf("  • Rate Limits:\n")
	fmt.Printf("    - General: %d req/min\n", config.GeneralRateLimit)
	fmt.Printf("    - Applications: %d req/min\n", config.ApplicationRateLimit)
	fmt.Println()
}
