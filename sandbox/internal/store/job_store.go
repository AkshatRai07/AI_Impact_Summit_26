package store

import (
	"sync"

	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/data"
	"github.com/AkshatRai07/AI_Impact_Summit_26/internal/models"
)

// JobStore manages the in-memory job data
type JobStore struct {
	jobs   map[string]models.Job
	jobIDs []string // Ordered list of job IDs for consistent iteration
	mu     sync.RWMutex
}

// NewJobStore creates a new job store with seed data
func NewJobStore() *JobStore {
	store := &JobStore{
		jobs:   make(map[string]models.Job),
		jobIDs: make([]string, 0),
	}

	// Load seed jobs
	seedJobs := data.GetSeedJobs()
	for _, job := range seedJobs {
		store.jobs[job.ID] = job
		store.jobIDs = append(store.jobIDs, job.ID)
	}

	return store
}

// GetAll returns all jobs with optional limit
func (s *JobStore) GetAll(limit int) []models.Job {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]models.Job, 0, len(s.jobs))

	count := 0
	for _, id := range s.jobIDs {
		if limit > 0 && count >= limit {
			break
		}
		if job, exists := s.jobs[id]; exists {
			result = append(result, job)
			count++
		}
	}

	return result
}

// GetByID returns a job by its ID
func (s *JobStore) GetByID(id string) (models.Job, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	job, exists := s.jobs[id]
	return job, exists
}

// GetCount returns total number of jobs
func (s *JobStore) GetCount() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.jobs)
}

// Search searches jobs by query (simple substring match in title, company, description)
func (s *JobStore) Search(query string, limit int) []models.Job {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if query == "" {
		return s.GetAll(limit)
	}

	result := make([]models.Job, 0)
	count := 0

	for _, id := range s.jobIDs {
		if limit > 0 && count >= limit {
			break
		}

		job := s.jobs[id]
		// Simple case-insensitive search
		if containsIgnoreCase(job.Title, query) ||
			containsIgnoreCase(job.Company, query) ||
			containsIgnoreCase(job.Description, query) {
			result = append(result, job)
			count++
		}
	}

	return result
}

// FilterByRemote returns only remote jobs
func (s *JobStore) FilterByRemote(limit int) []models.Job {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]models.Job, 0)
	count := 0

	for _, id := range s.jobIDs {
		if limit > 0 && count >= limit {
			break
		}

		job := s.jobs[id]
		if job.IsRemote || job.Remote {
			result = append(result, job)
			count++
		}
	}

	return result
}

// FilterByJobType returns jobs of a specific type
func (s *JobStore) FilterByJobType(jobType string, limit int) []models.Job {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]models.Job, 0)
	count := 0

	for _, id := range s.jobIDs {
		if limit > 0 && count >= limit {
			break
		}

		job := s.jobs[id]
		if job.JobType == jobType {
			result = append(result, job)
			count++
		}
	}

	return result
}

// containsIgnoreCase checks if s contains substr (case-insensitive)
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
