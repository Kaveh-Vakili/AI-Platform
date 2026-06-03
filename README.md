cd /Users/kavehvakili/Documents/STRATOS/AI-Platform
python3 - << 'PYEOF'
content = '''# STRATOS AI

> A governed, document-grounded AI briefing and agent orchestration platform.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![pgvector](https://img.shields.io/badge/pgvector-0.4-orange)
![Claude](https://img.shields.io/badge/Claude-Haiku-purple)

---

## What is STRATOS AI?

STRATOS AI is a full-stack platform where users upload business documents, ask grounded questions, and run reusable governed agent workflows that produce executive-ready briefings with citations, audit trails, token/cost accounting, and a hallucination-risk verdict on every output.

**Who it is for:** consultants, analysts, founders, investors, and ops teams who need defensible, source-grounded AI output from their own documents — and who care *how* the AI reached its conclusion, not just what it said.

**Why it is more than a RAG chatbot:** A basic RAG app answers a question. STRATOS treats generation as a governed industrial process with typed agents, declarative workflow templates, per-run cost accounting, and hallucination risk scoring baked into the pipeline.

---

## What is Built (Current State)

### Phase 1 — Foundation & Auth ✅
- FastAPI backend with PostgreSQL database
- Full SQLAlchemy schema (15 tables) including token_usage_logs and hallucination_checks
- JWT authentication: register, login, get current user
- Docker-based Postgres + pgvector setup

### Phase 2 — Document Pipeline ✅
- Workspace management (create, list)
- PDF upload with local file storage
- Automatic PDF parsing with pypdf
- Token-aware chunking (400 token chunks, 50 token overlap) with tiktoken
- Document status tracking: uploaded → parsing → ready

### Phase 3 — RAG Pipeline ✅
- OpenAI text-embedding-3-small embeddings (1536 dimensions)
- pgvector storage with IVFFlat cosine similarity index
- Semantic retrieval: embed query → find top-k similar chunks
- Grounded chat endpoint: Claude Haiku answers questions using only retrieved chunks
- Every claim tagged with source chunk ID
- Token usage tracked per request

### Phase 4 — Agent Harness (Logic Layer) ✅
- BaseAgent abstract class with shared RunContext
- AgentRegistry: typed agent registration and lookup
- WorkflowEngine: declarative template execution with persisted state
- Human approval checkpoints (pause/resume)
- Halt-on-error with partial artifact retention
- Three workflow templates: Executive Briefing, Risk Review, Investor Memo
- Three agents implemented: DocumentResearch, ExecutiveBriefing, TokenHallucinationControl
- Token ledger: running cost total across all LLM calls in a run
- Hallucination checker: claim-to-source alignment scoring (0-1)
- 9 passing tests with FakeLLM and FakeRepo (no DB or network needed)

---

## Architecture



┌─────────────────────────────────────────────────┐
│ Frontend (React/TS — Phase 5)                    │
└───────────────┬─────────────────────────────────┘
│ REST + JWT
┌───────────────▼─────────────────────────────────┐
│ FastAPI Backend                                  │
│  /auth  /workspaces  /documents  /chat           │
│  /workflows  /monitoring  /audit (Phase 5)       │
│                                                  │
│  ┌─────── Agent Harness ───────────────────┐     │
│  │ WorkflowEngine → AgentRegistry          │     │
│  │ TokenLedger → HallucinationChecker      │     │
│  └─────────────────────────────────────────┘     │
└───┬──────────────┬──────────────┬───────────────┘
│              │              │
┌───▼───┐    ┌─────▼─────┐  ┌────▼────┐
│Postgres│    │ pgvector  │  │ Uploads │
│15 tables│   │ embeddings│  │  /local │
└────────┘    └───────────┘  └─────────┘


---

## Agent Harness

The harness turns a declarative workflow template into an executed, logged run.

- **Agents** are Python classes subclassing `BaseAgent`, registered by `agent_type`
- **Workflow templates** are data (JSON), not code — new workflows need no redeploy
- **RunContext** is a shared mutable object threaded between agents — agents never call each other directly
- **Every LLM call** goes through `BaseAgent.llm()` so token usage is always captured
- **State is persisted** after every step — runs are resumable from the database alone
- **Approval gates** pause a run at `awaiting_approval` until a user POSTs approve/reject

---

## Token & Hallucination Monitoring

Two dedicated database tables capture governance data on every run:

**token_usage_logs** — one row per LLM call
- Tracks prompt tokens, completion tokens, estimated cost per model
- Aggregated per run for cost summary dashboard

**hallucination_checks** — one row per output review
- Source alignment score (0-1): how well claims match retrieved chunks
- Risk level: low / medium / high
- Unsupported claims: list of claims with no matching source
- Missing citations: supported claims that lack inline citation tags
- Recommended rewrite: safer version grounded only in available sources

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite (Phase 5) |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy 2.0 |
| Vector search | pgvector (IVFFlat cosine index) |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | Anthropic Claude Haiku |
| Auth | JWT (python-jose), bcrypt (passlib) |
| PDF parsing | pypdf |
| Chunking | tiktoken (cl100k_base) |
| Dev infra | Docker, uvicorn, pytest |

---

## Local Setup

### Prerequisites
- Python 3.11+
- Docker Desktop
- OpenAI API key
- Anthropic API key

### 1. Clone and enter the repo
```bash
git clone https://github.com/Kaveh-Vakili/AI-Platform.git
cd AI-Platform
```

### 2. Start the database
```bash
docker run --name stratos-db \\
  -e POSTGRES_USER=stratos \\
  -e POSTGRES_PASSWORD=stratos \\
  -e POSTGRES_DB=stratos \\
  -p 5432:5432 -d pgvector/pgvector:pg16
```

### 3. Set up the backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 4. Create your .env file


DATABASE_URL=postgresql+psycopg://stratos:stratos@localhost:5432/stratos
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key


### 5. Start the server
```bash
uvicorn app.main:app --reload
```

### 6. Run the tests
```bash
python -m pytest -v
```

All 9 tests pass with no database or API keys required.

### 7. Enable pgvector
```bash
docker exec -it stratos-db psql -U stratos -d stratos -c "
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(1536);
"
```

---

## API Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| POST | /auth/register | Create account |
| POST | /auth/login | Get JWT token |
| GET | /auth/me | Current user |

### Workspaces
| Method | Path | Description |
|---|---|---|
| POST | /workspaces | Create workspace |
| GET | /workspaces | List your workspaces |

### Documents
| Method | Path | Description |
|---|---|---|
| POST | /workspaces/{id}/documents | Upload PDF |
| GET | /workspaces/{id}/documents | List documents |
| DELETE | /workspaces/{id}/documents/{doc_id} | Delete document |

### RAG & Chat
| Method | Path | Description |
|---|---|---|
| POST | /workspaces/{id}/embed | Embed all chunks |
| POST | /workspaces/{id}/chat | Grounded chat |

---

## Roadmap

### Phase 5 — Workflow API (next)
- POST /workflows/run — execute a workflow against real documents
- GET /workflow-runs/{id} — run status and agent execution trace
- GET /workflow-runs/{id}/token-usage — per-run cost breakdown
- GET /workflow-runs/{id}/hallucination-checks — risk verdicts
- Repo facade: replace FakeRepo with real SQLAlchemy writers

### Phase 6 — Briefing Generation & Output History
- Executive briefing generation end to end
- Output history table
- Audit log API
- Agent execution timeline

### Phase 7 — Frontend & Deployment
- React/TypeScript command center UI
- Workflow run status with agent timeline
- Token/cost dashboard
- Hallucination risk indicator
- AWS or Render deployment
- CI/CD with GitHub Actions

---

## Resume Bullets

> Built STRATOS AI, a full-stack governed agent-orchestration platform (React/TypeScript + FastAPI/PostgreSQL + pgvector RAG) that executes multi-agent document-briefing workflows with per-run token/cost accounting and a dedicated hallucination-control agent that scores source alignment and flags unsupported claims before output ships.

> Designed and implemented an agent harness and workflow engine that registers typed agents, executes declarative workflow templates with persisted per-step state, supports human-approval checkpoints and resumable runs, and emits a full audit trail for every execution.

> Engineered an end-to-end RAG pipeline (chunking → embeddings → pgvector retrieval → citation validation) with claim-to-source alignment scoring, exposing token-cost and hallucination-risk data on every generated output.

---

## Project Structure

AI-Platform/
├─ backend/
│  ├─ app/
│  │  ├─ agents/          # BaseAgent, registry, core agents, control agent
│  │  ├─ api/             # auth, workspaces, documents, chat routers
│  │  ├─ core/            # config, security (JWT + bcrypt)
│  │  ├─ monitoring/      # token logger, hallucination checker, persistence hooks
│  │  ├─ rag/             # embeddings, retrieval, RAG pipeline
│  │  ├─ services/        # document parsing and chunking service
│  │  ├─ workflow/        # engine, templates
│  │  ├─ models.py        # all 15 SQLAlchemy tables
│  │  └─ main.py          # FastAPI app entry point
│  ├─ tests/              # 9 passing tests (FakeLLM, FakeRepo)
│  └─ pyproject.toml
├─ docs/
│  └─ STRATOS_AI_BUILD_PLAN.md
└─ README.md
