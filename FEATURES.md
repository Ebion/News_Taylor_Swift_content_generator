# Features — Persona-Driven Agentic Content Generator

This document summarizes the key features implemented for the take-home assignment.

> Assignment brief: Build a backend AI agentic workflow using two datasets (BBC news + Taylor Swift tweets) that:
> 1) Understands/extracts defining characteristics (style, tonality, structure)
> 2) Drafts content matching those characteristics (strong prompt engineering)
> 3) Provides review + QA (and evals if appropriate)

---

## 1) Two persona pipelines (BBC vs Taylor Swift)

The backend supports **two distinct persona pipelines**, selectable per request:

- `bbc` → news-article style
- `taylor_swift` → tweet/announcement style

Persona selection happens at the API boundary (`POST /generate`) and is carried through the entire run state.

---

## 2) Characterization Agent (style extraction)

### Purpose
Before writing, the system extracts defining characteristics from persona examples.

### Implementation highlights
- **Runtime sampling** from the provided datasets (no long-lived caching).
- **Characterization output** is persisted into run state as `CharacterizationDNA`.
- The extracted style guide mirrors the notebook design with keys:
  - `Tone`
  - `Structure`
  - `Punctuation Quirk`
  - `Vocabulary Level`
  - `Formatting`
  - `Key Phrases`

### Where in code
- Sampling: `services/data_loader.py`
- Agent: `agents/characterization_agent.py`
- Prompt: `agents/prompts/characterization.py`

---

## 3) Writer Agent (draft generation)

### Purpose
Generate persona-matching content for a user-provided topic.

### Implementation highlights
- Uses the extracted **Style DNA** to guide generation.
- Uses OpenAI **Responses API** with the `web_search` tool enabled (per notebook) to support time-sensitive topics.

### Where in code
- Agent: `agents/writer_agent.py`
- Prompt: `agents/prompts/writer.py`

---

## 4) Reviewer Agent (QA / evaluation)

### Purpose
Cross-check the generated draft against the Style DNA and produce structured feedback.

### Implementation highlights
- Returns a structured `ReviewOutput`:
  - `overall_fidelity_score` (1–10)
  - `violations[]` with `{aspect, issue, suggestion}`
  - `critique_summary`

### Where in code
- Agent: `agents/reviewer_agent.py`
- Prompt: `agents/prompts/reviewer.py`
- Models: `utils/review_models.py`

---

## 5) Rewriter Agent (human-in-the-loop iteration)

### Purpose
Produce a revised version based on:
- user comments
- selected reviewer violation indices

### Implementation highlights
- Appends a new version (`version + 1`) instead of overwriting history.
- Stores rewrite metadata (`based_on_version`, accepted indices, checks).

### Where in code
- Agent: `agents/rewriter_agent.py`
- Prompt: `agents/prompts/rewriter.py`
- Models: `utils/rewrite_models.py`

---

## 6) Run-scoped, file-backed persistence (versioning + auditability)

### Purpose
Support a stateless API while preserving run history and enabling repeatable review/rewrite loops.

### Implementation highlights
- One run state per JSON file:
  - `db/proj_<project_id>_run_<run_id>.json`
- Full version history under `versions[]`.
- Versioning rules enforced:
  - generate → version 1
  - review modifies latest version only
  - rewrite appends new version only

### Concurrency safety
- File locking with `filelock`
- Atomic writes using temp file + `os.replace`

### Where in code
- State models: `app/domain/models.py`
- Persistence: `services/run_store.py`

---

## 7) Stateless API endpoints (agent workflow orchestration)

### Purpose
Each request is stateless; state is reconstructed from disk via `{project_id, run_id}`.

### Endpoints
- `POST /generate`
  - creates a new run + version 1
- `POST /projects/{project_id}/runs/{run_id}/review`
  - reviews latest version and stores `review_artifact`
- `POST /projects/{project_id}/runs/{run_id}/rewrite`
  - appends a new version based on selected reviewer feedback + user comments

### Where in code
- Routers: `app/routers/`
- Orchestration: `services/workflow.py`
- FastAPI entrypoint: `app/main.py`

---

## 8) Prompt hygiene and separation of concerns

All prompts are separated into dedicated files under:

`agents/prompts/`

This keeps:
- prompts versionable and reviewable
- agent code focused on I/O + orchestration

---

## 9) Logging (debug + cost visibility)

LLM calls are logged to JSON files under `logging/` via `utils/logging_utils.py`.

Captured fields include:
- timestamp
- task name
- model
- truncated prompt/output
- token usage (when available)
- estimated cost

---

## Notes / Future extensions (optional)

- Add `GET /projects/{project_id}/runs/{run_id}` to fetch full state
- Add unit + integration tests with OpenAI calls mocked
- Strengthen rewrite QA checks (fact/markdown validation)
