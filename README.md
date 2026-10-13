# NexusFlow

NexusFlow is a local-first workspace for turning a software idea into structured, human-reviewable project plans and artifacts. It combines a Next.js frontend, a FastAPI API, saved workflow decisions, and an optional read-only MCP server.

> **Project status:** early-stage prototype for local development and evaluation. It is not production-hardened and should not be exposed to the public internet.

## What you can do

- Create projects and generate a structured idea brief.
- Move through persisted workflow stages, prepare Markdown drafts, edit them into new versions, and approve or reject each stage.
- Resume a saved workflow after closing or restarting the local app.
- Choose a project starter and adapt a reusable workflow template before starting.
- Record cited research sources, findings, and review status; refresh a versioned research plan from that log.
- Edit the structured brief and attach resolvable, version-linked review comments to artifacts.
- Review versioned artifacts, evaluations, trace events, and guardrail findings.
- Export a project package with the brief, workflow decisions, source log, unresolved review feedback, and full artifact version history.
- Optionally let an MCP-compatible local client read project context and artifacts.

The workflow is human-reviewed, but it is **not yet a distributed multi-agent system**. The Idea Analyst supports mock responses, Groq, and Amazon Bedrock; later stage drafts are generated from saved project inputs. Research sources are entered by project participants; NexusFlow does not fetch or independently verify them. Evaluation reports use deterministic rules rather than a model-based evaluator. Reviewer names are labels only because authentication is not implemented. See [the architecture notes](docs/ARCHITECTURE.md) for implementation boundaries.

## Quick start

### Requirements

- Python 3.10 or newer
- Node.js 20.9 or newer
- npm

### 1. Start the API

From the repository root:

```bash
cd backend
cp ../.env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The example configuration selects a mock provider that returns a predictable sample brief and does not require cloud credentials. The API creates a local SQLite database at `backend/nexusflow.db`. Check that the API is ready at <http://localhost:8000/health>; interactive API docs are at <http://localhost:8000/docs>.

### 2. Start the web app

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:3000>. The frontend uses `http://localhost:8000` by default. To point it at a different API, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` and restart the frontend.

### 3. Try the sample journey

On an empty dashboard, choose **Explore with a sample** to create a saved example project. From there, generate its brief, start the workflow, prepare and review drafts, record decisions, and inspect or export the resulting artifacts. The sample still uses your local API and database; it is not a hosted demo or pre-populated fixture.

To use your own idea instead, choose **Start your own** and create a project.

## Optional: local MCP server

In a third terminal, with the backend environment active:

```bash
cd backend
source .venv/bin/activate
python -m app.mcp_server
```

The Streamable HTTP endpoint is <http://127.0.0.1:8001/mcp>. It binds to loopback and exposes three read-only tools: `get_project_context`, `list_project_artifacts`, and `read_project_artifact`. It cannot change project data, start workflows, or perform external research. **A2A is not implemented.**

## Use Groq for idea analysis

After the Quick start has created `backend/.env`, set these values there:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Restart the API after changing the provider. The API sends idea analysis to Groq and validates the JSON response against the project brief schema. The selected model supports JSON output; check Groq's [current model list](https://console.groq.com/docs/models) if you choose a different model. Keep the key in the backend environment only. Never add a real key to `frontend/.env.local`, source control, or a public issue.

Groq returns prompt and completion token counts. NexusFlow shows the latest counts beside the generated brief and stores them in **Agent Runs** and **Metrics**. The cost dashboard's estimate is for Bedrock pricing only; Groq usage is counted but its cost is left blank rather than calculated with the wrong provider's rates.

To use Bedrock instead, set `LLM_PROVIDER=bedrock` and provide AWS credentials, region, and model settings. Use `LLM_PROVIDER=mock` to try the app without an external LLM key.

### Token limits and parallel tool calls

The idea analysis request caps the generated completion at 1,200 tokens. Parallel tool calling is not used by this request: it makes one model call and has no independent tools to invoke. Parallel calls can reduce waiting when several independent tools are needed, but they do not by themselves lower token consumption. For this workflow, controlling prompt and completion size is the relevant token limit.

## Configuration

| Variable | Purpose | Quick-start value / app fallback |
| --- | --- | --- |
| `LLM_PROVIDER` | Idea analysis provider (`mock`, `groq`, or `bedrock`) | `mock` in `.env.example`; app fallback is `bedrock` |
| `GROQ_API_KEY` | Backend-only Groq credential | Required when `LLM_PROVIDER=groq` |
| `GROQ_MODEL` | Groq chat completion model | `openai/gpt-oss-120b` |
| `DATABASE_URL` | SQLAlchemy database connection | `sqlite:///./nexusflow.db` |
| `AWS_REGION` | Bedrock region | `us-west-2` |
| `BEDROCK_MODEL_ID` | Bedrock model identifier | Set in `backend/app/config.py` |
| `CORS_ORIGINS` | Allowed browser origins | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | API URL used by frontend | `http://localhost:8000` |

Backend settings are read from environment variables or `backend/.env`. Frontend variables must use the `NEXT_PUBLIC_` prefix only when they are safe to expose in the browser.

## Architecture and roadmap

- [Architecture and current capabilities](docs/ARCHITECTURE.md)
- [Implementation status and follow-up plan](docs/IMPLEMENTATION_PLAN.md)
- [Product requirements and longer-term direction](docs/PRD.md)
- [Contributing guide](CONTRIBUTING.md)

The repository does not currently include a `LICENSE` file. Add the license you intend before presenting it as open source or accepting reuse contributions.

## Security and data

This prototype has no user authentication or project-level access control. Treat locally stored project data as untrusted and sensitive. Keep the API, database, and MCP server on a trusted development machine; do not expose them to an untrusted network. Do not store production secrets in this repository. Review the code and deployment requirements before using it with real customer or regulated data.
