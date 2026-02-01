# Job Portal Sandbox

A Go-based sandbox job portal for testing autonomous job search and auto-apply agents. This sandbox simulates a real job portal with job listings, application forms, and submission receipts.

## Features

- **50+ Realistic Job Listings**: Entry-level to senior positions across various tech companies
- **Full Application API**: Submit applications with resume, cover letter, and custom answers
- **Application Tracking**: Track application status and get receipts
- **Rate Limiting**: Configurable rate limits to simulate real-world scenarios
- **Failure Simulation**: Optional failure injection for testing retry logic
- **Health Checks**: Kubernetes-ready health endpoints

## Quick Start

### Running Locally

```bash
# Navigate to sandbox directory
cd sandbox

# Download dependencies
go mod tidy

# Run the server
go run main.go
```

The server will start on `http://localhost:8080`

### Running with Docker

```bash
# Build the image
docker build -t job-portal-sandbox .

# Run the container
docker run -p 8080:8080 job-portal-sandbox
```

### Running with Docker Compose (from project root)

```bash
docker-compose up sandbox
```

## API Endpoints

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/live` | GET | Liveness check |
| `/api` | GET | API documentation |
| `/api/stats` | GET | Sandbox statistics |

### Jobs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List all jobs |
| `/api/jobs?limit=N` | GET | List jobs with limit |
| `/api/jobs?q=query` | GET | Search jobs |
| `/api/jobs?remote=true` | GET | Filter remote jobs |
| `/api/jobs?type=internship` | GET | Filter by job type |
| `/api/jobs/:id` | GET | Get job details |
| `/api/jobs/:id/requirements` | GET | Get job requirements |
| `/api/jobs/search?q=query` | GET | Search jobs |

### Applications

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/applications` | POST | Submit application |
| `/api/applications` | GET | List applications |
| `/api/applications?email=X` | GET | List by email |
| `/api/applications/:id` | GET | Get application status |
| `/api/applications/:id/receipt` | GET | Get application receipt |
| `/api/applications/:id/status` | PATCH | Update status (testing) |

## Application Submission

### Request Format

```json
POST /api/applications
Content-Type: application/json

{
    "job_id": "job_001",
    "applicant_name": "John Doe",
    "applicant_email": "john@example.com",
    "resume": "Full resume text here...",
    "cover_letter": "Optional cover letter...",
    "phone": "+1-555-0100",
    "linkedin": "https://linkedin.com/in/johndoe",
    "portfolio": "https://johndoe.dev",
    "github": "https://github.com/johndoe",
    "work_authorization": "US Citizen",
    "sponsorship_needed": false,
    "start_date": "2026-06-01",
    "availability": "full-time",
    "salary_expectation": "$150,000",
    "relocation_willing": true,
    "remote_preference": "hybrid",
    "custom_answers": {
        "why_company": "I'm passionate about...",
        "biggest_challenge": "Once I faced..."
    }
}
```

### Response Format

```json
{
    "success": true,
    "confirmation_id": "CONF-20260201-abc12345",
    "application_id": "CONF-20260201-abc12345",
    "status": "received",
    "message": "Application submitted successfully.",
    "submitted_at": "2026-02-01T10:30:00Z",
    "job_id": "job_001",
    "job_title": "Software Engineer Intern",
    "company": "Google"
}
```

## Configuration

### Command Line Flags

```bash
./job-portal [flags]

Flags:
  -port int              Port to run the server on (default 8080)
  -failures              Enable failure simulation for testing
  -failure-rate float    Failure rate 0.0-1.0 (default 0.05)
  -slowdown-rate float   Slowdown rate 0.0-1.0 (default 0.03)
  -timeout-rate float    Timeout rate 0.0-1.0 (default 0.02)
  -rate-limit int        General rate limit per minute (default 100)
  -app-rate-limit int    Application rate limit per minute (default 30)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | 8080 |

### Testing with Failure Simulation

To test retry logic in your agent:

```bash
# Enable failures with 10% failure rate
go run main.go -failures -failure-rate 0.10
```

## Rate Limiting

The sandbox implements rate limiting to simulate real-world conditions:

- **General endpoints**: 100 requests/minute per IP
- **Application submissions**: 30 requests/minute per IP

When rate limited, you'll receive:

```json
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
    "error": "rate_limit_exceeded",
    "message": "Too many requests. Please wait before trying again.",
    "code": 429
}
```

## Job Data

The sandbox includes 50+ realistic job postings from companies like:

- Google, Microsoft, Apple, Meta
- Stripe, Airbnb, Netflix, Spotify
- OpenAI, Anthropic, DeepMind
- And many more...

Jobs include:
- Internships (entry-level)
- Full-time positions (1-8+ years experience)
- Remote and on-site options
- Various locations (US, UK, Remote)

## Integration with Backend

The sandbox is designed to work with the Python backend's `SandboxAPIClient`:

```python
from app.tools.sandbox_api import SandboxAPIClient

client = SandboxAPIClient()

# Fetch jobs
jobs = await client.fetch_jobs()

# Submit application
result = await client.submit_application({
    "job_id": "job_001",
    "applicant_name": "John Doe",
    "applicant_email": "john@example.com",
    "resume": "...",
    "cover_letter": "..."
})

# Check status
status = await client.get_application_status(result["confirmation_id"])
```

## Project Structure

```
sandbox/
├── main.go                    # Entry point
├── go.mod                     # Go modules
├── Dockerfile                 # Docker configuration
├── README.md                  # This file
└── internal/
    ├── data/
    │   └── jobs.go            # Seed job data
    ├── handlers/
    │   ├── applications.go    # Application endpoints
    │   ├── health.go          # Health endpoints
    │   └── jobs.go            # Job endpoints
    ├── middleware/
    │   ├── common.go          # Common middleware
    │   ├── failure_simulator.go # Failure injection
    │   └── rate_limiter.go    # Rate limiting
    ├── models/
    │   ├── application.go     # Application types
    │   └── job.go             # Job types
    ├── router/
    │   └── router.go          # Route setup
    └── store/
        ├── application_store.go # In-memory app storage
        └── job_store.go       # In-memory job storage
```

## License

Part of the Impact Summit Hackathon project.
