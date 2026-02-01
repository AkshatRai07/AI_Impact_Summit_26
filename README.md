# 🚀 ArbeitAI - Autonomous Job Application Agent

> **Fully autonomous AI agent that creates student artifact packs, searches and ranks jobs, and auto-applies at scale — all within explicit safety constraints.**

[![Built with LangGraph](https://img.shields.io/badge/Built%20with-LangGraph-blue?style=for-the-badge)](https://langchain.com/langgraph)
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Gemini-orange?style=for-the-badge)](https://ai.google.dev/)

---

## 🎯 What We Built

**Arbeit** is a student-facing AI agent that runs a complete **search-to-apply pipeline** without per-application human approval. The system is **safe-by-design**: it only applies within explicit constraints and never invents credentials.

### The Complete Flow

```
📄 Resume Upload → 🤖 Artifact Pack Generation → 🔍 Job Search & Ranking → ✍️ Auto-Personalization → 🔒 Safety Check → 📤 Auto-Apply → 📋 Real-time Tracking
```

---

## ✅ Requirements Satisfied

| Requirement | Status | Implementation |
|-------------|:------:|----------------|
| **Student Artifact Pack Generator** | ✅ | LLM-powered PDF parsing with facts-only extraction |
| - Structured Profile (JSON) | ✅ | Pydantic models for education, experience, projects, skills |
| - Bullet Bank | ✅ | Normalized achievement bullets tied to specific experiences |
| - Answer Library | ✅ | Reusable answers for common application questions |
| - Proof Pack | ✅ | Linked artifacts (GitHub, portfolio, demos) backing claims |
| - Constraints | ✅ | Location, remote preference, visa, start date |
| **Job Search + Ranking Agent** | ✅ | Hybrid semantic + rule-based matching |
| - Multi-source search | ✅ | Sandbox portal with 30+ realistic jobs |
| - Deduplication | ✅ | Tracks applied jobs, prevents re-applications |
| - Ranked Apply Queue | ✅ | Match scores with detailed explanations |
| **Auto-Personalization + Auto-Apply** | ✅ | End-to-end autonomous application submission |
| - Tailored resume variants | ✅ | LLM reorders/rephrases bullets per job |
| - Cover letter generation | ✅ | Job-specific recruiter notes |
| - Requirement-to-evidence mapping | ✅ | Each requirement linked to grounded bullet/proof |
| - Auto-submit with retries | ✅ | 3-retry logic with exponential backoff |
| - Rate limit handling | ✅ | Detects 429 errors and waits |
| - Application tracker | ✅ | Real-time status: queued/submitted/failed/retried |
| **Autonomy Constraints (Policy System)** | ✅ | Student-defined guardrails enforced by agent |
| - Max applications per day | ✅ | Configurable limit (default: 50) |
| - Minimum match threshold | ✅ | Only applies above threshold (default: 30%) |
| - Blocked companies | ✅ | Never applies to blacklisted companies |
| - Blocked role types | ✅ | Filters out unwanted roles (e.g., "senior", "manager") |
| - Location/remote constraints | ✅ | Enforces geographic preferences |
| - Kill switch | ✅ | Immediate stop capability |
| **Job Portal Sandbox** | ✅ | Full Go implementation for demo |
| - Realistic job listings | ✅ | 30+ jobs: Google, Stripe, Airbnb, Meta, etc. |
| - Application API | ✅ | POST /api/applications with validation |
| - Submission receipts | ✅ | Confirmation IDs returned |
| - Duplicate detection | ✅ | 409 Conflict for re-applications |
| - Rate limiting | ✅ | Token bucket algorithm |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                             │
│  ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────┐  │
│  │  Resume  │ │   Profile   │ │    Policy    │ │   Live Application      │  │
│  │  Upload  │ │    View     │ │    Editor    │ │        Feed (SSE)       │  │
│  └────┬─────┘ └──────┬──────┘ └──────┬───────┘ └────────────┬────────────┘  │
│       │              │               │                      │               │
└───────┼──────────────┼───────────────┼──────────────────────┼───────────────┘
        │              │               │                      │
        ▼              ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI + LangGraph)                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        LangGraph Workflow                           │    │
│  │                                                                     │    │
│  │  ┌──────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────┐   │    │
│  │  │  Fetch   │─▶│ Personalize │─▶│  Map Evidence│─▶│  Safety  │   │    │
│  │  │  Jobs    │   │   (LLM)     │   │   (Ground)   │   │  Check   │   │    │
│  │  └──────────┘   └─────────────┘   └──────────────┘   └────┬─────┘   │    │
│  │       │                                                   │         │    │
│  │       │                                      ┌────────────┴──────┐  │    │
│  │       │                                      ▼                   ▼  │    │
│  │  ┌────▼────┐                           ┌──────────┐        ┌──────┐ │    │
│  │  │ Vector  │                           │  Apply   │        │ Skip │ │    │
│  │  │Embeddings│                          │ (Submit) │        │ Job  │ │    │
│  │  │(Gemini) │                           └────┬─────┘        └──────┘ │    │
│  │  └─────────┘                                │                       │    │
│  └─────────────────────────────────────────────┼───────────────────────┘    │
│                                                │                            │
│  ┌─────────────────────────────────────────────▼───────────────────────┐    │
│  │                    Application Tracker (Supabase)                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SANDBOX (Go + Gin)                                 │
│                                                                             │
│  ┌────────────────┐  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │  Job Listings  │  │  Application API    │  │   Rate Limiter          │   │
│  │  (30+ jobs)    │  │  POST /api/apps     │  │   (Token Bucket)        │   │
│  └────────────────┘  └─────────────────────┘  └─────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Grounding & Safety Design

### Zero Hallucination Policy

The resume parser enforces strict extraction rules:

```python
# From pdf_parser.py
"""
CRITICAL RULES:
1. NEVER invent, embellish, or assume any information
2. Extract ONLY what is explicitly stated in the resume
3. If information is not present, use null or empty arrays
4. All bullets must be direct quotes or close paraphrases from the resume
5. All proof links must be explicitly mentioned in the resume
"""
```

### Evidence Grounding Validation

Every claim in the personalized application is validated:

```python
# From evidence_mapper.py
# Check if grounded in bullet bank
if source in bullet_lookup:
    enriched["grounded"] = True
    enriched["source_details"] = {
        "type": "bullet",
        "source_name": bullet_lookup[source].get("source_name")
    }
```

### Policy Enforcement

The safety checker blocks applications that violate student-defined constraints:

```python
# From safety_checker.py
# 1. Check blocked companies
if company.lower() in blocked_companies:
    errors.append(f"SAFETY BLOCK: {company} is in blocked companies list")

# 2. Check match threshold
if match_score < min_threshold:
    errors.append(f"SAFETY BLOCK: Match score {match_score} below threshold")

# 3. Kill switch
if state.get("kill_switch", False):
    return {"logs": ["🛑 KILL SWITCH ACTIVATED"]}
```

---

## 🚀 Demo Flow (5 Minutes)

### Step 1: Import Resume → Generate Artifact Pack
- Upload PDF resume via drag-and-drop
- LLM extracts: profile, bullet bank (with sources), proof pack, answer library
- Review and edit the structured profile

### Step 2: Configure Apply Policy
- Set max applications per day (default: 50)
- Set minimum match threshold (default: 30%)
- Add blocked companies/role types
- Toggle kill switch

### Step 3: Run Autonomous Workflow
- Agent fetches 30+ jobs from sandbox
- Ranks using hybrid scoring (semantic + rule-based)
- Generates Apply Queue with match explanations

### Step 4: Watch Auto-Applications (Real-time)
- Live feed shows each application being processed
- Personalized cover letters generated per job
- Evidence mapping displayed for each requirement
- Submissions with confirmation IDs

### Step 5: Review Tracker
- See all applications: submitted, failed, retried
- View stored cover letters and evidence mappings
- Check success rate statistics

---

## 📁 Project Structure

```
├── backend/                    # FastAPI + LangGraph
│   ├── main.py                # App entry point
│   ├── app/
│   │   ├── api/routes/        # REST endpoints
│   │   │   ├── workflow.py    # Start/stop/status workflow
│   │   │   ├── resume.py      # Upload and parse
│   │   │   └── tracker.py     # Application history
│   │   ├── graph/             # LangGraph workflow
│   │   │   ├── workflow.py    # Main workflow definition
│   │   │   ├── state.py       # AgentState TypedDict
│   │   │   └── nodes/         # Workflow nodes
│   │   │       ├── job_fetcher.py      # Fetch + rank jobs
│   │   │       ├── personalizer.py     # Tailored resume/cover letter
│   │   │       ├── evidence_mapper.py  # Ground claims
│   │   │       ├── safety_checker.py   # Policy enforcement
│   │   │       └── applicator.py       # Submit with retries
│   │   ├── core/
│   │   │   ├── embeddings.py  # Gemini vector embeddings
│   │   │   └── llm.py         # LLM configuration
│   │   ├── schemas/           # Pydantic models
│   │   │   ├── student.py     # StudentProfile, Bullet, ProofItem
│   │   │   └── policy.py      # ApplyPolicy
│   │   ├── tools/
│   │   │   ├── pdf_parser.py  # Resume extraction
│   │   │   └── sandbox_api.py # Sandbox client
│   │   └── db/
│   │       └── tracker.py     # Application persistence
│
├── frontend/                   # Next.js 14 + TypeScript
│   └── src/
│       ├── components/
│       │   ├── Dashboard.tsx           # Main 4-step wizard
│       │   ├── ResumeUpload.tsx        # PDF upload
│       │   ├── ProfileView.tsx         # Artifact pack display
│       │   ├── PolicyEditor.tsx        # Constraint configuration
│       │   ├── LiveApplicationFeed.tsx # Real-time SSE feed
│       │   └── ApplicationTracker.tsx  # Status history
│       └── lib/
│           └── api.ts                  # API client
│
├── sandbox/                    # Go + Gin job portal
│   ├── main.go                # Entry point
│   └── internal/
│       ├── data/jobs.go       # 30+ seed jobs
│       ├── handlers/
│       │   ├── jobs.go        # GET /api/jobs
│       │   └── applications.go # POST /api/applications
│       ├── middleware/
│       │   └── rate_limiter.go # Token bucket
│       └── store/             # In-memory storage
│
└── docker-compose.yml         # Full stack deployment
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, LangGraph, Python 3.11 |
| **AI/LLM** | Google Gemini (gemini-2.0-flash-001) |
| **Embeddings** | Gemini text-embedding-004 |
| **Database** | Supabase (with in-memory fallback) |
| **Sandbox** | Go 1.21, Gin framework |
| **Real-time** | Server-Sent Events (SSE) |
| **Containerization** | Docker, Docker Compose |

---

## 🏃 Running the Demo

### Prerequisites
- Docker & Docker Compose
- Google AI API Key (Gemini)
- Supabase project (optional, has fallback)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/arbeit.git
cd arbeit

# 2. Set environment variables
cp backend/.env.example backend/.env
# Edit .env with your GOOGLE_API_KEY

# 3. Start all services
docker-compose up --build

# 4. Access the app
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Sandbox:  http://localhost:8080
```

### Manual Setup

```bash
# Terminal 1: Sandbox (Go)
cd sandbox
go run main.go
# Running on :8080

# Terminal 2: Backend (Python)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 3: Frontend (Next.js)
cd frontend
npm install
npm run dev
# Running on :3000
```

---

## 📊 Test Bundle

### Sample Student Profile
Upload any PDF resume, or use the test resume in `test-data/sample_resume.pdf`

### Sample Jobs (in Sandbox)
The sandbox includes 30+ jobs across:
- Software Engineering (Google, Stripe, Airbnb)
- Data Science (Meta, Netflix)
- Product Management (Notion, Figma)
- Entry-level to Senior roles

### Demo Commands
```bash
# Check sandbox health
curl http://localhost:8080/health

# List available jobs
curl http://localhost:8080/api/jobs

# View submitted applications
curl http://localhost:8080/api/applications
```

---

## 👥 Team

Built with ❤️ for Impact Summit Hackathon

---

## 📄 License

MIT License - see [LICENSE](LICENSE)
