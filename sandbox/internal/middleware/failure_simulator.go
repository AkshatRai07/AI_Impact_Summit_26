package middleware

import (
	"math/rand"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// FailureSimulator simulates various failure scenarios for testing
type FailureSimulator struct {
	enabled          bool
	failureRate      float64 // 0.0 to 1.0
	slowdownRate     float64 // 0.0 to 1.0
	slowdownDuration time.Duration
	timeoutRate      float64 // 0.0 to 1.0
	rng              *rand.Rand
}

// NewFailureSimulator creates a new failure simulator
func NewFailureSimulator(failureRate, slowdownRate, timeoutRate float64) *FailureSimulator {
	return &FailureSimulator{
		enabled:          true,
		failureRate:      failureRate,
		slowdownRate:     slowdownRate,
		slowdownDuration: 5 * time.Second,
		timeoutRate:      timeoutRate,
		rng:              rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// Disable disables the failure simulator
func (fs *FailureSimulator) Disable() {
	fs.enabled = false
}

// Enable enables the failure simulator
func (fs *FailureSimulator) Enable() {
	fs.enabled = true
}

// SetFailureRate sets the failure rate (0.0 to 1.0)
func (fs *FailureSimulator) SetFailureRate(rate float64) {
	fs.failureRate = rate
}

// FailureMiddleware creates a middleware that randomly simulates failures
func FailureMiddleware(simulator *FailureSimulator) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !simulator.enabled {
			c.Next()
			return
		}

		// Only apply to application submissions (POST /api/applications)
		if c.Request.Method == "POST" && c.Request.URL.Path == "/api/applications" {
			roll := simulator.rng.Float64()

			// Check for timeout simulation
			if roll < simulator.timeoutRate {
				time.Sleep(30 * time.Second)
				c.AbortWithStatusJSON(http.StatusGatewayTimeout, gin.H{
					"error":   "timeout",
					"message": "Request timed out. Please try again.",
					"code":    504,
				})
				return
			}

			// Check for slowdown simulation
			if roll < simulator.timeoutRate+simulator.slowdownRate {
				time.Sleep(simulator.slowdownDuration)
			}

			// Check for random failure
			if roll < simulator.timeoutRate+simulator.slowdownRate+simulator.failureRate {
				statusCode := randomErrorCode(simulator.rng)
				c.AbortWithStatusJSON(statusCode, gin.H{
					"error":   "simulated_failure",
					"message": "Simulated failure for testing. Please retry.",
					"code":    statusCode,
				})
				return
			}
		}

		c.Next()
	}
}

// randomErrorCode returns a random HTTP error code
func randomErrorCode(rng *rand.Rand) int {
	codes := []int{
		http.StatusInternalServerError, // 500
		http.StatusBadGateway,          // 502
		http.StatusServiceUnavailable,  // 503
	}
	return codes[rng.Intn(len(codes))]
}
