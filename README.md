# NexusFlow

NexusFlow turns an early software idea into a structured brief, reviewable planning documents, and an exportable project package. It pairs a Next.js workspace with a FastAPI backend, SQLite persistence for local development, optional LLM-backed idea analysis, deterministic review checks, explicit human approvals, and project-level team access.

> **Status:** local-first prototype for development and evaluation. It includes email/password accounts and project roles, but lacks account recovery, email delivery, production-grade session handling, and operational hardening. Do not expose it to the public internet as-is.

## Contents

- [What NexusFlow does](#what-nexusflow-does)
- [Current boundaries](#current-boundaries)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Project workflow](#project-workflow)
- [LLM providers and token usage](#llm-providers-and-token-usage)
- [Local MCP server](#local-mcp-server)
- [Configuration reference](#configuration-reference)
- [API overview](#api-overview)
- [Tests and production build](#tests-and-production-build)
- [Data, security, and troubleshooting](#data-security-and-troubleshooting)
- [Roadmap and contributing](#roadmap-and-contributing)

## What NexusFlow does

- Create and update software projects, then generate and edit a structured idea brief.
- Start a persisted workflow using a selected template and stage sequence.
- Prepare Markdown deliverables, edit them as new versions, and review changes over time.
- Record explicit approvals, rejections, requests for changes, and revisits.
- Use a combined review queue for workflow stages and standalone human review checkpoints.
- Create accounts, invite collaborators using single-use links, and assign owner, editor, reviewer, or viewer access per project.
- Gate workflow approvals on the expected artifact, minimum content, high/critical content findings, unresolved comments, unresolved blocking guardrails, and new artifact versions after revision requests.
- Record user-curated research sources, findings, notes, and review status; refresh a versioned research plan from that log.
- Run deterministic consistency and Devil's Advocate evaluations and inspect guardrail findings and agent run records.
- Export a ZIP package containing the brief, workflow decisions, research source log, review feedback, and artifact version history.
- Optionally expose read-only project context and artifacts to a local MCP-compatible client.

The interface includes a project dashboard and workspace, brief editor, workflow and decision history, artifacts, research, evaluations, traces, standalone checkpoints, a review queue, and MLOps views for runs, prompts, and metrics.

## Current boundaries

NexusFlow is a **human-reviewed project planning workflow**, not a distributed multi-agent system. The Idea Analyst is the only model-backed agent flow. Workflow stages produce transparent drafts from saved project inputs; they do not represent independent agents collaborating. Research source entry is user-curated; the app does not discover or verify sources. Evaluation reports are rule-based rather than model-based.

Groq and Bedrock are provider options for idea analysis. The development example uses a mock provider so the app can run without cloud credentials. Token counts are recorded when the provider returns them. The cost summary currently estimates Bedrock costs only, so Groq cost is intentionally left blank. Parallel tool calling is not used for idea analysis because that flow makes a single model request and has no independent tool calls to run.

MCP currently provides read-only local access. Since MCP does not yet carry the signed-in user's identity, the server refuses to expose projects shared with multiple members; keep it local. **A2A is not implemented.** See [Architecture](docs/ARCHITECTURE.md) and [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) for detail.

## Architecture

```text
Next.js 16 / React 19 frontend (port 3000)
        │ HTTP / JSON
        ▼
FastAPI backend (port 8000)
  ├─ REST API routers with signed bearer-token authentication and project-role checks
  ├─ services: workflow, artifacts, reviews, research, guardrails, evaluations, MLOps
  ├─ Idea Analyst: mock / Groq / Amazon Bedrock
  └─ SQLAlchemy persistence
        │
        ▼
SQLite database (local default: backend/nexusflow.db)

Optional local MCP Streamable HTTP server (127.0.0.1:8001/mcp)
  └─ read-only project context and artifact tools
```

The backend is organized into `api/`, `agents/`, `guardrails/`, `models/`, `schemas/`, and `services/`. The frontend is a Next.js App Router application under `frontend/src/app/`, with reusable components under `frontend/src/components/` and typed API clients under `frontend/src/lib/`.

SQLite tables persist projects, briefs, workflow plans and decisions, artifacts and versions, source records, review comments, HITL checkpoints, guardrail findings, evaluations, traces, prompt versions, and agent runs. The application initializes tables on startup; this prototype does not include a production migration workflow.

Account tables store password hashes, project membership roles, and invitation token hashes. Tokens expire after 12 hours. In an existing single-user local database, the first account registered claims previously unowned projects. This is a convenience migration for local data, not an appropriate ownership policy for a multi-tenant production database.

## Requirements

- Python 3.10 or newer
- Node.js 20.9 or newer and npm
- Optional: a Groq API key or AWS credentials for non-mock idea analysis

## Quick start

Open two terminals from the repository root.

### 1. Backend API

```bash
cd backend
cp ../.env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The example `.env` selects `LLM_PROVIDER=mock`, so no model credentials are needed. The API creates the SQLite file at `backend/nexusflow.db` when started from `backend/`. Verify it at <http://localhost:8000/health>; interactive API documentation is at <http://localhost:8000/docs>.

### 2. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:3000>. The frontend uses `http://localhost:8000` by default. To change this, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local`, then restart the frontend. Only put values safe for browser exposure in `NEXT_PUBLIC_*` variables.

### 3. Try the project journey

From the dashboard, choose **Explore with a sample** to create a saved example project, or **Start your own** to enter an idea. Generate the brief, start the workflow, prepare the stage draft, review the artifact, and record your decision. Continue through stages and use the Review Queue to see items needing attention. The sample is created in your local database; it is not a hosted demo or preloaded fixture.

On first run, create an account from the sign-in page. The first account on an existing local database becomes owner of its legacy projects. To collaborate, open a project's **Team** tab, create an invitation for a teammate's email, copy the link, and share it. The invited person must sign in or register using that email and accept the invitation. NexusFlow does not send invitation email yet.

### Project roles

| Role | Access |
| --- | --- |
| Owner | Full access, delete project, manage members and invitations |
| Editor | Read and change project content, artifacts, research, and workflow setup |
| Reviewer | Read project data, record workflow/HITL decisions, comment, and resolve review findings |
| Viewer | Read-only project access |

The API returns 404 for projects the signed-in account cannot access. New projects automatically make their creator the owner.

## Project workflow

The default full-product stage sequence is:

| Stage | Prepared deliverable(s) | What the current implementation does |
| --- | --- | --- |
| Idea discovery | Idea Brief | Uses the saved structured brief; generate the brief with idea analysis first. |
| Market research | Research Plan | Builds a plan from the idea and participant-entered sources. It does not browse the web. |
| Technical feasibility | Technical Feasibility | Creates a transparent initial planning draft from project inputs. |
| PRD and architecture | Product Requirements, Architecture Outline | Creates initial Markdown outlines from project inputs and brief. |
| Quality review | Quality Review | Collects deterministic consistency and Devil's Advocate findings. |
| Final approval | Final Package Guide | Lists the project's saved artifacts for final human review. |

Every stage requires a human decision. The backend prevents approval until the stage deliverables exist and pass the configured review checks. A request for changes requires notes; before a later approval, every required artifact must have a version newer than that request. Preparing an existing stage preserves its current artifact and reviewer edits rather than silently overwriting them.

Workflow templates store a stage plan on the project workflow. The frontend offers starter choices and lets users choose a workflow sequence; valid stage keys are `idea_discovery`, `market_research`, `technical_feasibility`, `prd_architecture`, `quality_review`, and `final_approval`.

Standalone HITL checkpoints are a separate mechanism alongside workflow stage approvals. Both appear in the combined review experience.

## LLM providers and token usage

Provider configuration is read by the backend from its process environment or `backend/.env`.

### Mock (default for local setup)

`LLM_PROVIDER=mock` returns a predictable sample brief and requires no API key. Use this for UI exploration and tests.

### Groq

Set these values in `backend/.env`:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Restart the API after changing provider configuration. The backend sends idea analysis to Groq and validates the returned structured data against the brief schema. Check Groq's [current model documentation](https://console.groq.com/docs/models) for available models and capabilities. Keep the key in the backend environment only; never commit it or put it in a frontend environment file.

When returned by the provider, input and output token counts appear with idea analysis and are stored in Agent Runs and Metrics. Idea analysis currently makes one model request and caps completion output at 1,200 tokens. Parallel tool calling does not reduce token use and is not used in this request because there are no independent tool calls.

### Amazon Bedrock

Set `LLM_PROVIDER=bedrock`, configure `AWS_REGION` and `BEDROCK_MODEL_ID`, and provide AWS credentials through the environment or the AWS credential chain used by boto3. Do not commit access keys. The application fallback provider is Bedrock, but `.env.example` selects mock for a credential-free first run.

## Local MCP server

Start the API first, then open a third terminal:

```bash
cd backend
source .venv/bin/activate
python -m app.mcp_server
```

The Streamable HTTP endpoint is <http://127.0.0.1:8001/mcp>. It binds to loopback and exposes three read-only tools:

- `get_project_context(project_id)` — project idea, brief, workflow state, and decisions.
- `list_project_artifacts(project_id)` — artifact names, types, versions, and update times.
- `read_project_artifact(project_id, artifact_id)` — latest artifact content after checking that the artifact belongs to the supplied project.

These tools cannot edit or delete data, approve workflow stages, create projects, or perform external research. The server is a local development integration; it has no authentication for network exposure. A2A and connections to external MCP servers are not implemented.

## Configuration reference

Backend variables can be set in `backend/.env` or in the backend process environment. See [.env.example](.env.example) for a copyable template.

| Variable | Purpose | Example / fallback |
| --- | --- | --- |
| `APP_NAME` | Application name setting | `NexusFlow` |
| `APP_ENV` | Environment label | `development` |
| `DEBUG` | Debug setting | `true` |
| `BACKEND_HOST` | Configured backend host | `0.0.0.0` in settings; local quick start explicitly binds to `127.0.0.1` |
| `BACKEND_PORT` | Configured backend port | `8000` |
| `DATABASE_URL` | SQLAlchemy connection URL | `sqlite:///./nexusflow.db` |
| `CORS_ORIGINS` | JSON list of permitted browser origins | `["http://localhost:3000"]` |
| `LLM_PROVIDER` | Idea-analysis provider (`mock`, `groq`, `bedrock`) | app fallback `bedrock`; `.env.example` uses `mock` |
| `GROQ_API_KEY` | Backend-only Groq credential | empty unless Groq is selected |
| `GROQ_MODEL` | Groq model identifier | `openai/gpt-oss-120b` |
| `AWS_REGION` | AWS region for Bedrock | `us-west-2` |
| `BEDROCK_MODEL_ID` | Bedrock model identifier | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| `LLM_TIMEOUT_SECONDS` | Provider request timeout setting | `60` |
| `AUTH_SECRET_KEY` | JWT signing key; set a stable random value for deployment | random per process if omitted locally |
| `AUTH_TOKEN_EXPIRE_MINUTES` | Account session lifetime | `720` |
| `NEXT_PUBLIC_API_URL` | Frontend API base URL | `http://localhost:8000` |

`DATABASE_URL` may be pointed at another SQLAlchemy database, but the project only documents and validates SQLite for local use. Other database engines may require a driver, schema migrations, and deployment-specific configuration.

## API overview

All routes except health, account registration, and login require `Authorization: Bearer <access_token>`. The complete request and response schemas are available in Swagger UI at <http://localhost:8000/docs>.

| Area | Representative routes |
| --- | --- |
| Health | `GET /health` |
| Accounts | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/invitations/accept` |
| Projects and brief | `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}`, `POST/GET/PUT /projects/{id}/idea-analysis` |
| Project team | `GET /projects/{id}/members`, `POST/GET/DELETE /projects/{id}/invitations`, member role/removal and ownership-transfer routes |
| Workflow | `POST/GET /projects/{id}/workflow`, `POST /projects/{id}/workflow/prepare`, `POST /projects/{id}/workflow/decision`, `GET /review-queue/workflows` |
| Artifacts and export | `GET/POST /projects/{id}/artifacts`, artifact version routes, `GET /projects/{id}/package/export` |
| Research | `GET/POST /projects/{id}/research-sources`, source update/delete routes, `POST /projects/{id}/research-plan/refresh` |
| Review and HITL | project checkpoint routes, `GET /review-queue`, artifact review comment routes |
| Evaluations and guardrails | consistency and Devil's Advocate evaluation routes; guardrail finding routes |
| Runs and metrics | `/mlops/runs`, `/mlops/prompts`, `/mlops/cost-summary`, `/mlops/metrics` |
| Traces and dashboard | project trace routes, `/dashboard/stats`, and `/dashboard/events/{project_id}` |

Routes generally return JSON. Artifact package and artifact export routes return downloadable files. Project-level API routes require membership and enforce role permissions.

## Tests and production build

Run backend tests from `backend/` with the project virtual environment active:

```bash
source .venv/bin/activate
LLM_PROVIDER=mock DATABASE_URL=sqlite:///./test-nexusflow.db pytest -q
```

Run frontend checks from `frontend/`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```

The backend test command uses a separate SQLite filename so it does not use the normal local database. Remove that file when it is no longer needed. Tests use the mock provider and should not require a paid model key.

## Data, security, and troubleshooting

- Local projects and workflow records are stored in `backend/nexusflow.db` when using the documented quick start. Back up or remove that file to manage local state.
- `.env`, `.venv`, and local SQLite database files are ignored by Git. `.env.example` contains placeholders, not credentials.
- Email/password accounts and project roles are implemented, but account verification, password reset, login rate limiting, invitation email delivery, organization management, and production session revocation are not. Do not put sensitive customer data into a shared or exposed deployment.
- The frontend stores bearer tokens in browser local storage. Use a production identity provider and secure HttpOnly cookie/session design before operating an internet-facing service.
- Keep the API and MCP server bound to trusted local interfaces. Do not expose port 8000 or 8001 to the public internet.
- CORS is not authentication. Restricting `CORS_ORIGINS` does not prevent non-browser clients from calling the API.
- SQLite table creation occurs at app startup; there is no migration history or production backup/restore workflow yet.
- Groq/AWS credentials belong only in the backend environment. If a credential is accidentally committed or shared, revoke and rotate it.
- Set a stable high-entropy `AUTH_SECRET_KEY` in each deployment. If omitted, a random process-local key is generated; API restarts invalidate tokens, and multiple workers will not share sessions.

Common local checks:

1. If the web app cannot reach the API, confirm the backend health endpoint and `NEXT_PUBLIC_API_URL`.
2. If the browser reports a CORS error, ensure the frontend origin appears in the backend `CORS_ORIGINS` JSON list, then restart the API.
3. If Groq analysis fails, confirm `LLM_PROVIDER`, the backend-only API key, model availability, and provider connectivity.
4. If stage approval is blocked, read the returned `review_issues`, prepare the current stage, review required artifacts, resolve feedback or blocking findings, and create new artifact versions after a change request.

## Roadmap and contributing

Current next steps for making the project safer and more useful include account recovery and verification, secure production sessions, database migrations and backup strategy, CI, end-to-end browser coverage, real source discovery with citations and explicit permission controls, model-aware cost estimates, and a deployment guide. A2A should be considered when independent agents actually need cross-service task handoff.

- [Architecture and current capabilities](docs/ARCHITECTURE.md)
- [Implementation status and follow-up plan](docs/IMPLEMENTATION_PLAN.md)
- [Product requirements and longer-term direction](docs/PRD.md)
- [Contributing guide](CONTRIBUTING.md)

There is currently no `LICENSE` file. Choose and add a license before describing this repository as open source or accepting contributions under a particular reuse grant.
