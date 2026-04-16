# Persona-Driven Agentic Content Generator

A stateless FastAPI backend implementing a **multi-agent workflow** that generates, reviews, and rewrites content in the voice of a chosen persona.

Supported personas:
- `bbc` — news-article style
- `taylor_swift` — tweet/announcement style

---

## What it does

The system runs a **generate → review → rewrite → repeat** loop:

1. **Characterize** — samples examples from a persona dataset and extracts a Style DNA (tone, structure, vocabulary, punctuation quirks, key phrases)
2. **Write** — generates a draft on a user-provided topic, guided by the Style DNA and optionally augmented with live web search
3. **Review** — scores the draft against the Style DNA (1–10 fidelity score) and surfaces structured violations
4. **Rewrite** — accepts selected violations + user comments and produces a revised version, appending it to the run history

All run state is persisted to JSON files on disk (`db/`) with file locking and atomic writes, so the API itself is fully stateless.

---

## Architecture overview

```
persona_content_generator/
  app/
    main.py                  # FastAPI entrypoint
    routers/                 # generate / review / rewrite routes
    schemas/                 # HTTP request/response models
    domain/                  # Persisted run-state models (RunState, VersionState, DNA)
  agents/
    prompts/                 # Prompt templates (one file per agent)
    characterization_agent.py
    writer_agent.py
    reviewer_agent.py
    rewriter_agent.py
  services/
    workflow.py              # Orchestration logic
    run_store.py             # File DB + locking + atomic writes
    data_loader.py           # CSV sampling per persona
    llm_service.py           # OpenAI calls + logging wrapper
  utils/                     # Shared models and utilities
  artifact/                  # Notebook-produced style guide artifacts
  db/                        # Run state JSON files + lock files
  logging/                   # LLM call logs (JSON, with token usage + cost)
  notebooks/                 # Experiment notebooks used to validate agents
  ui/
    chatbot.py               # Streamlit frontend
```

---

## Quickstart

### Docker (recommended)

```bash
# 1. Copy and configure environment
cp env.example .env          # macOS/Linux
copy env.example .env        # Windows

# Edit .env:
# OPENAI_API_KEY=sk-...
# LLM_MODEL_NAME=gpt-4o-mini

# 2. Start everything
docker compose up --build
```

- FastAPI: http://localhost:8000 (docs: http://localhost:8000/docs)
- Streamlit UI: http://localhost:8501

Run state (`db/`), logs (`logging/`), and artifacts (`artifact/`) are bind-mounted and survive restarts.

```bash
docker compose down
```

### Manual (Windows)

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt

copy env.example .env
# set OPENAI_API_KEY and LLM_MODEL_NAME in .env

# Terminal 1 — API
python -m uvicorn app.main:app --reload

# Terminal 2 — UI
streamlit run ui\chatbot.py
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate` | Create a new run and generate version 1 |
| `POST` | `/projects/{project_id}/runs/{run_id}/review` | Review the latest version |
| `POST` | `/projects/{project_id}/runs/{run_id}/rewrite` | Rewrite based on violations + comments |

### Examples

```bash
# Generate
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"A quantum computing breakthrough","persona":"bbc"}'

# Review
curl -X POST http://127.0.0.1:8000/projects/<project_id>/runs/<run_id>/review

# Rewrite
curl -X POST http://127.0.0.1:8000/projects/<project_id>/runs/<run_id>/rewrite \
  -H "Content-Type: application/json" \
  -d '{"accepted_violation_indices":[0,2],"user_comments":"Make the headline sharper."}'
```

---

## Using the Streamlit UI

1. Open http://localhost:8501
2. Select a persona (`bbc` or `taylor_swift`)
3. Type a topic and press **Enter** to generate a draft
4. Click **Request review** on the draft to get a fidelity score and violation list
5. Tick violations, type rewrite instructions, and press **Enter** to produce a new version
6. Repeat from step 4, or use **⚙️ Settings** to browse older versions or load a previous run

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for the full walkthrough.

---

## Persistence & logging

- Run state: `db/proj_<project_id>_run_<run_id>.json`
- LLM call logs: `logging/` — each entry captures timestamp, model, truncated prompt/output, token usage, and estimated cost

---

## Further reading

- [FEATURES.md](FEATURES.md) — detailed feature breakdown aligned to the assignment requirements
- [USAGE_GUIDE.md](USAGE_GUIDE.md) — step-by-step UI guide
