import streamlit as st

st.title("FastAPI Chatbot")

# Ensure ui/_utils.py can be imported when Streamlit runs this file directly
import os, sys
_THIS_DIR = os.path.dirname(__file__)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from _utils import api_get, api_post, apply_run_state, seed_messages_from_run
from components import render_settings_panel, render_chat_area

# Backend base URL (kept for backward compatibility in session_state)
API_BASE = "http://localhost:8000"

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_run = None
    st.session_state.selected_violation_indices = []
    st.session_state.user_comments = ""
    st.session_state.selected_version_index = None
    st.session_state.api_base = API_BASE
    st.session_state.topic = ""
    st.session_state.persona = None
    st.session_state.new_run_persona = "taylor_swift"

    # UI/UX state machine
    st.session_state.phase = "idle"  # idle | generating | awaiting_review_request | reviewing | awaiting_rewrite_comments | rewriting
    st.session_state.pending_action = None

# Top toolbar: keep settings button inline (no permanent right-side column that steals width)
toolbar_left, toolbar_right = st.columns([0.92, 0.08], vertical_alignment="top")
with toolbar_right:
    render_settings_panel()

# Main chat (full width)
render_chat_area()

# Status placeholder: ensures spinners/status appear right above the chat input.
status = st.empty()


def _set_phase(phase: str):
    st.session_state.phase = phase


def _set_pending(action: dict | None):
    st.session_state.pending_action = action


def _compute_phase_from_state():
    """Best-effort phase reconciliation based on current run + review selection."""
    if not st.session_state.get("current_run"):
        return "idle"

    # If we have a run, by default we wait for user to request review on the latest version.
    versions = st.session_state.current_run.get("versions", [])
    svi = st.session_state.get("selected_version_index")
    latest = None
    if versions and svi is not None and 0 <= svi < len(versions):
        latest = versions[svi]

    if latest and latest.get("review_artifact"):
        # Review exists. If user selected violations, we are ready for rewrite comments.
        if st.session_state.get("selected_violation_indices"):
            return "awaiting_rewrite_comments"
        return "awaiting_review_request"  # review exists but no violations picked yet; keep input disabled

    return "awaiting_review_request"


# If not currently running a job, keep phase consistent with state
if not st.session_state.get("pending_action") and st.session_state.get("phase") not in {
    "generating",
    "reviewing",
    "rewriting",
}:
    st.session_state.phase = _compute_phase_from_state()


# Execute queued work (second rerun) while UI is locked
pending = st.session_state.get("pending_action")
if pending:
    ptype = pending.get("type")
    if ptype == "generate":
        _set_phase("generating")
        with status.spinner("Starting run..."):
            resp = api_post(
                "/generate",
                json={"topic": pending.get("topic"), "persona": pending.get("persona")},
            )
        if resp.status_code == 200:
            body = resp.json() if resp.content else {}
            pid = body.get("project_id")
            rid = body.get("run_id")
            if pid and rid:
                with status.spinner("Loading run..."):
                    getr = api_get(f"/projects/{pid}/runs/{rid}")
                if getr.status_code == 200:
                    apply_run_state(st, getr.json())
                    _set_pending(None)
                    _set_phase("awaiting_review_request")
                    st.rerun()
                else:
                    st.error(f"Run created but failed to load: {getr.status_code} {getr.text}")
                    _set_pending(None)
                    _set_phase("idle")
            else:
                st.error("Generate succeeded but response was missing project_id/run_id — check backend response.")
                _set_pending(None)
                _set_phase("idle")
        else:
            st.error(f"Failed to start run: {resp.status_code} {resp.text}")
            _set_pending(None)
            _set_phase("idle")

    elif ptype == "review":
        _set_phase("reviewing")
        pid = pending.get("project_id")
        rid = pending.get("run_id")
        with status.spinner("Running review..."):
            resp = api_post(f"/projects/{pid}/runs/{rid}/review")
        if resp.status_code == 200:
            getr = api_get(f"/projects/{pid}/runs/{rid}")
            if getr.status_code == 200:
                apply_run_state(st, getr.json())
                _set_pending(None)
                _set_phase(_compute_phase_from_state())
                st.rerun()
            else:
                st.error(f"Review completed but failed to reload run: {getr.status_code} {getr.text}")
                _set_pending(None)
                _set_phase("awaiting_review_request")
        else:
            st.error(f"Review failed: {resp.status_code} {resp.text}")
            _set_pending(None)
            _set_phase("awaiting_review_request")

    elif ptype == "rewrite":
        _set_phase("rewriting")
        pid = pending.get("project_id")
        rid = pending.get("run_id")
        payload = {
            "accepted_violation_indices": pending.get("accepted_violation_indices") or [],
            "user_comments": pending.get("user_comments") or "",
        }
        with status.spinner("Rewriting..."):
            resp = api_post(f"/projects/{pid}/runs/{rid}/rewrite", json=payload)
        if resp.status_code == 200:
            getr = api_get(f"/projects/{pid}/runs/{rid}")
            if getr.status_code == 200:
                apply_run_state(st, getr.json())
                _set_pending(None)
                # After rewrite, require a new review request for the new version.
                _set_phase("awaiting_review_request")
                st.rerun()
            else:
                st.error(f"Rewrite succeeded but failed to reload run: {getr.status_code} {getr.text}")
                _set_pending(None)
                _set_phase("awaiting_review_request")
        else:
            st.error(f"Rewrite failed: {resp.status_code} {resp.text}")
            _set_pending(None)
            _set_phase("awaiting_rewrite_comments")

    else:
        st.error(f"Unknown pending action: {pending}")
        _set_pending(None)
        _set_phase(_compute_phase_from_state())

busy = st.session_state.phase in {"generating", "reviewing", "rewriting"}

if st.session_state.phase == "idle":
    placeholder = "Send a topic to start a run"
elif st.session_state.phase == "awaiting_rewrite_comments":
    placeholder = "Rewrite comments (press Enter to submit)"
else:
    placeholder = "Waiting for review / processing..."

input_disabled = busy or st.session_state.phase in {"awaiting_review_request", "reviewing", "rewriting"}

# Chat input (first rerun): enqueue work and rerun immediately so user message appears instantly.
if prompt := st.chat_input(placeholder, disabled=input_disabled):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Enqueue appropriate action and rerun.
    if st.session_state.phase == "idle":
        _set_pending(
            {
                "type": "generate",
                "topic": prompt,
                "persona": st.session_state.new_run_persona,
            }
        )
        _set_phase("generating")
        st.rerun()

    if st.session_state.phase == "awaiting_rewrite_comments":
        run = st.session_state.current_run or {}
        _set_pending(
            {
                "type": "rewrite",
                "project_id": run.get("project_id"),
                "run_id": run.get("run_id"),
                "accepted_violation_indices": list(st.session_state.get("selected_violation_indices") or []),
                "user_comments": prompt,
            }
        )
        _set_phase("rewriting")
        st.rerun()
