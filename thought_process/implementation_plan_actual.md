# Implementation Plan (Actual) — FastAPI Agentic Content Generator

This file is the **execution blueprint** for implementing the system described in `thought_process/implementation_plan.md`, tailored to the **current repo state** (currently: notebooks + `utils/` helpers, but no FastAPI app yet).

It’s intended to be used as a progress tracker while we implement.

---

## Goal

Build a **run-scoped, stateless FastAPI backend** that:

- Generates a persona-driven draft from runtime CSV sampling + characterization
- Persists run state to JSON on disk (`db/`) using **file locking + atomic writes**
- Supports human-in-the-loop loop: **generate → review → rewrite → repeat**
- Enforces **structured outputs** for all LLM agent calls via Pydantic + OpenAI structured parsing
- Provides clear endpoint contracts and robust error handling

---

## Deliverables

### API Endpoints

- `POST /generate`
- `POST /projects/{project_id}/runs/{run_id}/review`
- `POST /projects/{project_id}/runs/{run_id}/rewrite`
- (Nice-to-have) `GET /projects/{project_id}/runs/{run_id}` (fetch entire run state)
- (Nice-to-have) `GET /health`

### Persistence

- Directory: `db/`
- One JSON file per run: `db/proj_{project_id}_run_{run_id}.json`
- Concurrency safety:
  - `filelock` per run file
  - atomic writes (temp file + rename)

### Agents

- Characterization agent (dynamic CSV ingestion)
- Writer agent (v1 draft)
- Reviewer agent (structured violations + score)
- Rewriter agent (applies selected feedback + user comments)

### Structured Outputs

- All agent calls via a central `call_structured_llm(...)` wrapper
- Strict Pydantic schema binding
- Reject malformed output; bounded retries (optional)

### Logging

- Log request payloads + LLM responses + parsed outputs
- Reuse/adapt `utils/logging_utils.py`

---

## Success Criteria

- `uvicorn` runs successfully.
- `POST /generate` returns `{project_id, run_id, version_number=1, content}` and creates a run JSON file.
- `POST /review` attaches `review_artifact` to the **latest** version.
- `POST /rewrite` appends a **new version** (version + 1) and never overwrites history.
- Re-review / re-rewrite works repeatedly (always operates on latest version).
- Concurrent operations on the same run do not corrupt JSON.

---

## Repo State (What Exists Today)

- ✅ `utils/review_models.py` (`ReviewOutput`, `StyleViolation`)
- ✅ `utils/rewrite_models.py` (`RewriteOutput`)
- ✅ `utils/style_manager.py` (loads `artifact/style_guides.json`)
- ✅ `utils/logging_utils.py` (JSON logging + OpenAI/LangChain helpers)
- ❌ No FastAPI app code yet
- ❌ No `db/` persistence layer yet
- ❌ No agent modules yet

---

## Key Design Choices (Implementation-Level)

1. **Package layout (recommended)**
   - `app/` → FastAPI entrypoint + HTTP schemas + routes
   - `services/` → file DB, orchestration, LLM wrapper, data loading
   - `agents/` → stateless agent modules + prompts

2. **Draft content normalization**
   - Persist drafts in `versions[].content` (string)
   - If rewrite agent returns `rewritten_content`, store that as `content` and store the remaining fields under `rewrite_metadata`.

3. **CSV schema variability**
   - Implement loader with **env-configurable column names** (since CSV contents may change and are not hardcoded in code).

4. **Persona normalization**
   - Canonical personas: `bbc`, `taylor_swift`
   - Optionally support aliases mapping.

---

## Work Breakdown (Order of Implementation)

### Phase 1 — Project scaffolding + dependencies

- [x] Add Python dependency management (requirements.txt)
- [x] Install core deps: fastapi, uvicorn, openai, filelock, python-dotenv (opt)
- [x] Create package structure: `app/`, `services/`, `agents/`, `db/` (gitkeep)

**Exit criteria**: `uvicorn app.main:app --reload` runs; `/health` returns ok; repo has target directories.

---

### Phase 2 — Domain / persistence models

- [x] Create Pydantic models for run state:
  - [x] `RunState`
  - [x] `RunMetadata` (status, latest_version)
  - [x] `VersionState` (content, created_at, review_artifact, rewrite_metadata)
  - [x] `CharacterizationDNA` model (aligned to notebook style guide output)

**Exit criteria**: can create `RunState(...)` and `.model_dump_json()` it.

---

### Phase 3 — File DB layer (locking + atomic writes)

- [x] Implement `services/run_store.py`:
  - [x] `get_run_path(project_id, run_id)`
  - [x] `load_run(...)` (locked)
  - [x] `save_run(...)` (locked, atomic)
  - [ ] `create_run(...)` (optional helper; not required if workflow owns creation)
  - [x] `update_run(...)` helper (read-modify-write under same lock)

**Exit criteria**: create + load + update a run file without corruption.

---

### Phase 4 — LLM service wrapper (structured output)

- [x] Implement `services/llm_service.py`:
  - [x] OpenAI client creation from env
  - [x] `call_structured_llm(system_prompt, user_prompt, schema, model)`
  - [ ] bounded retry on parsing failures (optional)
  - [x] consolidated logging utilities (moved from `utils/logging_utils.py`)

**Exit criteria**: a trivial structured call works in isolation (can be tested with a dummy schema).

---

### Phase 5 — Data loader (dynamic CSV sampling)

- [ ] Implement `services/data_loader.py`:
  - [ ] `get_samples(persona, topic, n)`
  - [ ] runtime CSV load (no in-memory caching across requests)
  - [ ] persona-specific logic with env-configurable column mappings
  - [ ] chunked load strategy if needed

**Exit criteria**: can return `List[str]` samples for each persona.

---

### Phase 6 — Agents (stateless modules)

- [x] `agents/characterization_agent.py` → returns `CharacterizationDNA`
- [x] `agents/writer_agent.py` → returns `DraftOutput` (content)
- [x] `agents/reviewer_agent.py` → returns `utils.review_models.ReviewOutput`
- [x] `agents/rewriter_agent.py` → returns `utils.rewrite_models.RewriteOutput`
- [x] Store prompts under `agents/prompts/` (or as constants)

**Exit criteria**: each agent function runs given stub inputs and returns Pydantic output.

---

### Phase 7 — Orchestration (workflow engine)

- [x] Implement `services/workflow.py`:
  - [x] `generate(topic, persona)`
  - [x] `review(project_id, run_id)`
  - [x] `rewrite(project_id, run_id, accepted_indices, user_comments)`
- [x] Enforce versioning rules:
  - [x] generate → version 1
  - [x] review modifies latest version only
  - [x] rewrite appends version + 1 only
  - [x] rewrite requires review exists on latest version

**Exit criteria**: run lifecycle works end-to-end without HTTP.

---

### Phase 8 — FastAPI HTTP layer

- [ ] Implement `app/main.py` + routes:
  - [ ] `POST /generate`
  - [ ] `POST /projects/{project_id}/runs/{run_id}/review`
  - [ ] `POST /projects/{project_id}/runs/{run_id}/rewrite`
  - [ ] (optional) `GET /projects/{project_id}/runs/{run_id}`
  - [ ] (optional) `GET /health`
- [ ] HTTP request/response schemas in `app/schemas/`
- [ ] Map errors to HTTP codes (400/404/500)

**Exit criteria**: can call endpoints with curl and get expected responses.

---

### Phase 9 — Tests + DX (developer experience)

- [ ] Add unit tests:
  - [ ] persistence / versioning rules
  - [ ] index validation for rewrite
- [ ] Add integration tests with FastAPI `TestClient` with LLM calls mocked
- [ ] Provide run commands (e.g., `uvicorn app.main:app --reload`)

**Exit criteria**: `pytest` passes locally.

---

## Open Questions / Config To Finalize (Before Coding)

1. CSV column names:
   - BBC: text column? category column? date column?
   - Taylor: text column? likes/retweets columns?

2. Persona strings & aliases:
   - canonical: `bbc`, `taylor_swift`

3. Model choices per agent:
   - Char/Writer/Rewriter: `gpt-4o`
   - Reviewer: `gpt-4o-mini`

---

## Notes on Implementation Constraints

- CSV files are not to be cached across requests.
- Every request is stateless; state is reconstructed from disk.
- Structured output is mandatory for all agent calls.
- Concurrency safety is mandatory (locks + atomic writes).
