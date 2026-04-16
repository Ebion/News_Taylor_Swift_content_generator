import streamlit as st
from _utils import api_get, apply_run_state


def render_settings_panel():
    with st.popover("⚙️"):
        st.markdown("### Settings")

        # Run info + view-only version browser
        if st.session_state.get("current_run"):
            run = st.session_state.current_run
            st.markdown(
                f"**Project:** {run.get('project_id')}  \n"
                f"**Run:** {run.get('run_id')}  \n"
                f"**Latest version:** {run.get('runs_metadata', {}).get('latest_version')}"
            )

            if st.button("Refresh run", key="refresh_run_settings"):
                pid = run.get("project_id")
                rid = run.get("run_id")
                getr = api_get(f"/projects/{pid}/runs/{rid}")
                if getr.status_code == 200:
                    apply_run_state(st, getr.json())
                    st.success("Run refreshed")
                    st.rerun()
                else:
                    st.error(f"Failed to refresh run: {getr.status_code} {getr.text}")

            st.divider()
            st.markdown("#### Versions (view only)")
            versions = run.get("versions", [])
            if versions:
                # Display newest first
                options = [v.get("version_number") for v in versions if v.get("version_number") is not None]
                options_sorted = sorted(options, reverse=True)
                default_vn = run.get("runs_metadata", {}).get("latest_version")
                if default_vn not in options_sorted and options_sorted:
                    default_vn = options_sorted[0]
                selected_vn = st.selectbox(
                    "Select version",
                    options=options_sorted,
                    index=options_sorted.index(default_vn) if default_vn in options_sorted else 0,
                    key="view_version_number",
                )
                selected = next((v for v in versions if v.get("version_number") == selected_vn), None)
                if selected:
                    st.code(selected.get("content", ""))
            else:
                st.caption("No versions to display yet.")

        st.caption("Load an existing run by Project ID + Run ID. This will refresh the full UI state.")
        with st.form("load_run"):
            pid = st.text_input("Project ID")
            rid = st.text_input("Run ID")
            if st.form_submit_button("Load run"):
                if pid and rid:
                    resp = api_get(f"/projects/{pid}/runs/{rid}")
                    if resp.status_code == 200:
                        apply_run_state(st, resp.json())
                        st.success("Run loaded")
                        st.rerun()
                    else:
                        st.error(f"Failed to load run: {resp.status_code} {resp.text}")


def render_chat_area():
    # New-run controls live at the top of the chatbot
    if not st.session_state.current_run:
        st.markdown("**New run** — choose a persona, then send your first message (that message becomes the *topic* and will start the run).")
        st.session_state.new_run_persona = st.selectbox(
            "Persona",
            options=["taylor_swift", "bbc"],
            index=0 if st.session_state.new_run_persona == "taylor_swift" else 1,
        )

    # Styles: make only the *message list* scrollable.
    # Important: do NOT wrap the header/subheader inside `.chat-container`, otherwise Streamlit's
    # DOM structure can place the <h3> unexpectedly and you'll end up scrolling headers/controls.
    st.markdown(
        '''<style>
            .chat-container{
                max-height:calc(100vh - 240px);
                overflow:auto;
                padding:8px 12px 8px 12px;
                border:1px solid #eee;
                margin-top:0;
            }
            /* collapse extra selectbox spacing */
            .stSelectbox, .stSelectbox > div {margin-bottom:0 !important; padding-bottom:0 !important;}
        </style>''',
        unsafe_allow_html=True,
    )

    # Header: always show current project/run or 'new run' (keep this ABOVE the scroll container)
    st.subheader("Chat")
    header_pid = "new run"
    header_rid = "new run"
    if st.session_state.current_run:
        header_pid = st.session_state.current_run.get("project_id") or header_pid
        header_rid = st.session_state.current_run.get("run_id") or header_rid
    st.markdown("**Project:** " + str(header_pid))
    st.markdown("**Run:** " + str(header_rid))

    # Scrollable message list
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        role = message.get("role")
        content = message.get("content", "")

        # Streamlit chat UI doesn't have a native "system" role; rendering it as chat_message
        # can create odd artifacts (e.g. a lone "S"). Render system notes as info instead.
        if role == "system":
            st.info(content)
            continue

        with st.chat_message(role):
            st.markdown(content)
            # If this assistant message corresponds to the latest version content, show Request review
            if role == "assistant" and st.session_state.current_run:
                versions = st.session_state.current_run.get("versions", [])
                svi = st.session_state.selected_version_index
                if versions and svi is not None and 0 <= svi < len(versions):
                    latest_content = versions[svi].get("content")
                    if latest_content and latest_content.strip() == content.strip():
                        # only show review button if there's no review_artifact yet
                        if versions[svi].get("review_artifact") is None:
                            # Queue review action; actual API call is handled in ui/chatbot.py so we can
                            # lock input and show progress consistently.
                            if st.button(
                                "Request review",
                                key=f"request_review_v{versions[svi].get('version_number')}",
                            ):
                                pid = st.session_state.current_run.get("project_id")
                                rid = st.session_state.current_run.get("run_id")
                                st.session_state.pending_action = {
                                    "type": "review",
                                    "project_id": pid,
                                    "run_id": rid,
                                }
                                st.session_state.phase = "reviewing"
                                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Review / rewrite controls (remain in main chat)
    if st.session_state.current_run:
        versions = st.session_state.current_run.get("versions", [])
        svi = st.session_state.selected_version_index
        if svi is not None and versions and 0 <= svi < len(versions):
            version = versions[svi]
            if version.get("review_artifact"):
                ra = version.get("review_artifact")
                st.markdown("---")
                st.markdown(f"**Review — fidelity:** {ra.get('overall_fidelity_score')}")
                st.markdown("Select violations to accept for rewrite:")
                selected = []
                for i, v in enumerate(ra.get("violations", [])):
                    key = f"vio_v{version.get('version_number')}_{i}"
                    checked = st.checkbox(f"[{i}] {v.get('aspect')}: {v.get('issue')}", key=key)
                    if checked:
                        selected.append(i)
                st.session_state.selected_violation_indices = selected

                # Auto-enter rewrite-comments mode as soon as at least one violation is selected.
                if st.session_state.selected_violation_indices:
                    st.session_state.phase = "awaiting_rewrite_comments"
                    st.caption("Ready for rewrite comments below.")
                else:
                    # No violations selected yet; keep input disabled.
                    st.session_state.phase = "awaiting_review_request"





