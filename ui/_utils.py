import os
import requests
from typing import List, Dict, Any

# Backend base URL.
# - Local dev default: http://localhost:8000
# - Docker Compose: set API_BASE_URL=http://api:8000
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def api_post(path: str, json: Dict | None = None):
    return requests.post(API_BASE + path, json=json)


def api_get(path: str):
    return requests.get(API_BASE + path)


def seed_messages_from_run(run: Dict[str, Any]) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    if not run:
        return msgs
    topic = run.get("topic")
    persona = run.get("persona")
    pid = run.get("project_id")
    rid = run.get("run_id")
    latest = run.get("runs_metadata", {}).get("latest_version")
    msgs.append({"role": "system", "content": f"Loaded run {pid}/{rid} (persona={persona}, latest_version={latest})."})
    if topic:
        msgs.append({"role": "user", "content": str(topic)})
    versions = run.get("versions", [])
    idx = None
    if isinstance(latest, int) and versions:
        idx = max(0, min(latest - 1, len(versions) - 1))
    elif versions:
        idx = len(versions) - 1
    if idx is not None and versions:
        content = versions[idx].get("content")
        if content:
            msgs.append({"role": "assistant", "content": str(content)})
    return msgs


def apply_run_state(st, run: Dict[str, Any]):
    # set run and derived session state consistently
    st.session_state.current_run = run
    versions = run.get("versions", [])
    latest = run.get("runs_metadata", {}).get("latest_version", 1)
    st.session_state.selected_version_index = max(0, min(latest - 1, len(versions) - 1)) if versions else None
    st.session_state.selected_violation_indices = []
    st.session_state.user_comments = ""
    st.session_state.messages = seed_messages_from_run(run)
