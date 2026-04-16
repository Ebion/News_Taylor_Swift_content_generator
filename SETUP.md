# Persona-Driven Agentic Content Generator (persona_content_generator)

Stateless FastAPI backend implementing a **run-scoped agent workflow**:

**generate → review → rewrite → repeat**

State is persisted to JSON files on disk (`db/`) using **file locks + atomic writes**.

Personas supported:
- `bbc`
- `taylor_swift`

For a feature-by-feature breakdown aligned to the take-home requirements, see **[`FEATURES.md`](FEATURES.md)**.


## Docker Quickstart (recommended)

Prereqs:
- Docker Desktop (or Docker Engine) with **Docker Compose**

### 1) Create your `.env`

Copy `env.example` → `.env` and set your OpenAI key:

**macOS/Linux**
```bash
cp env.example .env
```

**Windows (cmd.exe)**
```bat
copy env.example .env
```

Edit `.env` and set:
```text
OPENAI_API_KEY=sk-...
LLM_MODEL_NAME=gpt-4o-mini
```

### 2) Start everything

From the repo root:
```bash
docker compose up --build
```

This starts:
- FastAPI at http://localhost:8000 (docs: http://localhost:8000/docs)
- Streamlit at http://localhost:8501

### 3) Persistent data

By default, Compose bind-mounts these folders so your run state + logs survive restarts:
- `db/` (run JSONs + lock files)
- `logging/` (LLM logs + full prompts)
- `artifact/` (notebook-produced artifacts)

To stop:
```bash
docker compose down
```

---

## Quickstart (Windows)

### 1) Create and activate a virtual environment (recommended)

**cmd.exe**
```bat
python -m venv .venv
.venv\Scripts\activate
```

**PowerShell**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2) Install dependencies
```bat
python -m pip install -r requirements.txt
```

### 2b) Install git hooks (recommended)

This repo uses **pre-commit** with **nbstripout** to automatically strip Jupyter notebook outputs on every commit.

> Note: Git hooks require a **one-time install per clone** (this is a Git limitation). After you run `pre-commit install`, the stripping happens automatically on future commits.

Install the hooks once per clone:
```bat
pre-commit install
```

Optional: run on all files once (useful if notebooks were committed before hooks were installed):
```bat
pre-commit run --all-files
```

If you want to see what the hook would do without making a commit:
```bat
pre-commit run nbstripout --all-files
```

Troubleshooting:
- If `pre-commit` is not found, make sure your venv is activated and re-run:
  ```bat
  python -m pip install -r requirements.txt
  ```
- If notebooks were already committed with outputs, run `pre-commit run --all-files` and commit the resulting changes.

### 3) Configure environment variables

Copy `env.example` to `.env` and set your key:
```text
OPENAI_API_KEY=sk-...
LLM_MODEL_NAME=gpt-4o-mini
```

Optional CSV path overrides (defaults shown):
```text
BBC_CSV_PATH=csv/bbc-news-data.csv
TAYLOR_SWIFT_CSV_PATH=csv/TaylorSwift13.csv
```

### 4) Run the API
```bat
python -m uvicorn app.main:app --reload
```

Open:
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### 5) Run the Streamlit UI

In a **new terminal** (keep the API running), start Streamlit:

```bat
streamlit run ui\chatbot.py
```

Open the UI:
- http://localhost:8501

For a step-by-step guide on using the frontend, see **[`USAGE_GUIDE.md`](USAGE_GUIDE.md)**.

---

## API Endpoints

### POST `/generate`
Creates a new run and returns **version 1**.

Example:
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d "{\"topic\":\"A quantum computing breakthrough\",\"persona\":\"bbc\"}"
```

### POST `/projects/{project_id}/runs/{run_id}/review`
Reviews the latest version and attaches a structured review artifact.

Example:
```bash
curl -X POST http://127.0.0.1:8000/projects/<project_id>/runs/<run_id>/review
```

### POST `/projects/{project_id}/runs/{run_id}/rewrite`
Rewrites latest version using selected reviewer violations + user comments, and appends a new version.

Example:
```bash
curl -X POST http://127.0.0.1:8000/projects/<project_id>/runs/<run_id>/rewrite \
  -H "Content-Type: application/json" \
  -d "{\"accepted_violation_indices\":[0,2],\"user_comments\":\"Make the headline sharper.\"}"
```

---

## Persistence & Logs

- Run state is stored under `db/`:
  - `db/proj_<project_id>_run_<run_id>.json`
  - `.lock` files are used to prevent concurrent corruption
- LLM call logs are stored under `logging/` as JSON

---

## Repo Layout (high level)


Rough structure:

```text
persona_content_generator/
  app/
    main.py                  # FastAPI app + OpenAPI metadata
    routers/                 # Route modules (generate/review/rewrite)
    schemas/                 # HTTP request/response models
    domain/                  # Persisted run-state models (RunState, VersionState, DNA)
  agents/
    prompts/                 # Prompt templates (one file per agent)
    characterization_agent.py
    writer_agent.py
    reviewer_agent.py
    rewriter_agent.py
  services/
    workflow.py              # generate → review → rewrite orchestration
    run_store.py             # File DB + locking + atomic writes
    data_loader.py           # CSV sampling per persona
    llm_service.py           # OpenAI structured calls + logging wrapper
  utils/                     # Shared models/utilities (review/rewrite models, logging utils)
  artifact/                  # Notebook-produced artifacts (style guides, samples)
  db/                        # File-backed run state (JSON per run) + .lock files
  logging/                   # LLM call logs (JSON)
  notebooks/                 # Experiment notebooks used to validate agents
  requirements.txt
  env.example
  README.md
  FEATURES.md
```
