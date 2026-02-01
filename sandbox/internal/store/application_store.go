package store

import (
	"fmt"
	"sync"
	"time"

	"github.com/AkshatRai07/ImpactSummitPrivate/internal/models"
	"github.com/google/uuid"
)

// ApplicationStore manages the in-memory application data
type ApplicationStore struct {
	applications     map[string]*models.Application
	applicationIDs   []string            // Ordered list for consistent iteration
	byJobID          map[string][]string // Index: job_id -> application_ids
	byApplicantEmail map[string][]string // Index: email -> application_ids
	mu               sync.RWMutex
}

// NewApplicationStore creates a new application store
func NewApplicationStore() *ApplicationStore {
	return &ApplicationStore{
		applications:     make(map[string]*models.Application),
		applicationIDs:   make([]string, 0),
		byJobID:          make(map[string][]string),
		byApplicantEmail: make(map[string][]string),
	}
}

// Create creates a new application and returns it
func (s *ApplicationStore) Create(req models.ApplicationRequest, job models.Job) (*models.Application, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Check for duplicate application (same email + same job)
	if existing, exists := s.byApplicantEmail[req.ApplicantEmail]; exists {
		for _, appID := range existing {
			if app, ok := s.applications[appID]; ok && app.JobID == req.JobID {
				return nil, fmt.Errorf("duplicate application: already applied to this job")
			}
		}
	}

	// Generate IDs
	id := uuid.New().String()
	confirmationID := fmt.Sprintf("CONF-%s-%s", time.Now().Format("20060102"), id[:8])

	now := time.Now()

	app := &models.Application{
		ID:                id,
		ConfirmationID:    confirmationID,
		ApplicationID:     confirmationID, // Alias
		JobID:             req.JobID,
		JobTitle:          job.Title,
		Company:           job.Company,
		ApplicantName:     req.ApplicantName,
		ApplicantEmail:    req.ApplicantEmail,
		Resume:            req.Resume,
		CoverLetter:       req.CoverLetter,
		Status:            models.StatusReceived,
		SubmittedAt:       now,
		UpdatedAt:         now,
		Phone:             req.Phone,
		LinkedIn:          req.LinkedIn,
		Portfolio:         req.Portfolio,
		GitHub:            req.GitHub,
		WorkAuthorization: req.WorkAuthorization,
		CustomAnswers:     req.CustomAnswers,
	}

	// Store the application
	s.applications[id] = app
	s.applicationIDs = append(s.applicationIDs, id)

	// Update indices
	s.byJobID[req.JobID] = append(s.byJobID[req.JobID], id)
	s.byApplicantEmail[req.ApplicantEmail] = append(s.byApplicantEmail[req.ApplicantEmail], id)

	return app, nil
}

// GetByID returns an application by its ID (supports both internal ID and confirmation ID)
func (s *ApplicationStore) GetByID(id string) (*models.Application, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// Try direct lookup
	if app, exists := s.applications[id]; exists {
		return app, true
	}

	// Try by confirmation ID
	for _, app := range s.applications {
		if app.ConfirmationID == id || app.ApplicationID == id {
			return app, true
		}
	}

	return nil, false
}

// GetByJobID returns all applications for a job
func (s *ApplicationStore) GetByJobID(jobID string) []*models.Application {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]*models.Application, 0)

	if ids, exists := s.byJobID[jobID]; exists {
		for _, id := range ids {
			if app, ok := s.applications[id]; ok {
				result = append(result, app)
			}
		}
	}

	return result
}

// GetByEmail returns all applications by an applicant email
func (s *ApplicationStore) GetByEmail(email string) []*models.Application {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]*models.Application, 0)

	if ids, exists := s.byApplicantEmail[email]; exists {
		for _, id := range ids {
			if app, ok := s.applications[id]; ok {
				result = append(result, app)
			}
		}
	}

	return result
}

// GetAll returns all applications
func (s *ApplicationStore) GetAll(limit int) []*models.Application {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]*models.Application, 0, len(s.applications))

	count := 0
	for _, id := range s.applicationIDs {
		if limit > 0 && count >= limit {
			break
		}
		if app, exists := s.applications[id]; exists {
			result = append(result, app)
			count++
		}
	}

	return result
}

// UpdateStatus updates the status of an application
func (s *ApplicationStore) UpdateStatus(id string, status models.ApplicationStatus, notes string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	app, exists := s.applications[id]
	if !exists {
		// Try by confirmation ID
		for _, a := range s.applications {
			if a.ConfirmationID == id {
				app = a
				exists = true
				break
			}
		}
	}

	if !exists {
		return fmt.Errorf("application not found")
	}

	app.Status = status
	app.Notes = notes
	app.UpdatedAt = time.Now()

	if status == models.StatusReviewing || status == models.StatusShortlisted || status == models.StatusRejected {
		now := time.Now()
		app.ReviewedAt = &now
	}

	return nil
}

// GetCount returns total number of applications
func (s *ApplicationStore) GetCount() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.applications)
}

// GetCountByJobID returns number of applications for a job
func (s *ApplicationStore) GetCountByJobID(jobID string) int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if ids, exists := s.byJobID[jobID]; exists {
		return len(ids)
	}
	return 0
}

// GetStats returns application statistics
func (s *ApplicationStore) GetStats() map[string]int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	stats := make(map[string]int)

	for _, app := range s.applications {
		stats[string(app.Status)]++
	}

	return stats
}
