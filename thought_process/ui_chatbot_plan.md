# Streamlit Chatbot — Integration Plan

Objective
-- Build a Streamlit UI (ui/chatbot.py) that integrates with the FastAPI backend to: generate drafts, request reviews, and perform rewrites. The UI must fetch run state from the backend (GET run), call existing endpoints (generate, review, rewrite), and allow users to select which reviewer violations to accept for rewrite.

High-level requirements
- Provide a Start-run experience where the **first chat message** becomes the topic and triggers POST /generate
- Provide a Persona selector (bbc / taylor_swift) that is selectable only before a run starts, then fixed
- Provide a way to load run state from backend: GET /projects/{project_id}/runs/{run_id}
- Provide a Review button that POSTs to /projects/{project_id}/runs/{run_id}/review and displays the returned review_artifact
- Provide a Rewrite panel where users can select violation indices and add comments, then POST to /projects/{project_id}/runs/{run_id}/rewrite
- Keep UI and backend separable (all interactions via HTTP endpoints)
- Maintain run and chat state in Streamlit session_state

Session state keys
- messages: list of chat messages (role/content)
- current_run: full run JSON (project_id, run_id, versions, runs_metadata, etc.)
- selected_version_index: index into current_run['versions'] (default latest_version - 1)
- selected_violation_indices: list[int]
- user_comments: str
- ui_mode: one of ["chat", "generate_form", "review_panel", "rewrite_panel"]

User flows
1. Load run
   - Call GET /projects/{project_id}/runs/{run_id} to populate current_run
2. Generate
   - User selects persona (bbc / taylor_swift)
   - User sends their **first chat message**; that message becomes the topic
   - UI calls POST /generate with {topic, persona}
   - On success, update current_run and messages
3. Review
   - POST /projects/{project_id}/runs/{run_id}/review
   - Display review_artifact.violations with checkboxes
4. Rewrite
   - User selects violations and provides comments
   - POST /projects/{project_id}/runs/{run_id}/rewrite with {accepted_violation_indices, user_comments}
   - On success, update current_run and show new version content

Error handling and UX
- Show spinners during network calls
- Validate user inputs (e.g., at least one violation selected before rewrite)
- Display backend errors (404, 400, 500) as user-friendly messages

Implementation TODOs
- [x] Review router endpoints and infer request/response expectations
- [x] Design session_state keys and UI layout
- [x] Implement Generate flow in ui/chatbot.py (first chat message starts run, API call, state updates)
- [x] Implement Review flow in ui/chatbot.py (call, display review artifact, selection UI)
- [x] Implement Rewrite flow in ui/chatbot.py (selection, call, update state)
- [x] Implement GET run flow in ui/chatbot.py (load run from backend)
- [x] Add backend GET endpoint: GET /projects/{project_id}/runs/{run_id}
- [x] Move run load into Settings popover and refresh app state on load
- [ ] Add general chat input behavior and integration with run context (beyond start-run topic)
- [ ] Add error handling, spinners, and UX polish

Notes
- Backend GET endpoint required: GET /projects/{project_id}/runs/{run_id} returning run JSON.
- If authentication or CORS is needed, add headers/CORS configuration later.

Prepared by: Cline
Date: 2026-02-22
