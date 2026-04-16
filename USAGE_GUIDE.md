#+#+#+#+--------------------------------------------------------------------
# Frontend Usage Guide (Streamlit)

This document explains how to use the Streamlit UI (`ui/chatbot.py`) to run the end-to-end workflow:

**generate → review → rewrite → repeat**

> Prerequisite: make sure the FastAPI backend is running on `http://127.0.0.1:8000`.

---

## 1) Start the UI

From the repo root:

```bat
streamlit run ui\chatbot.py
```

Open: http://localhost:8501

---

## 2) UI layout

### Chat area (main panel)

The main panel is the chat view:

- A **scrollable** message history
- A single chat input at the bottom (enabled/disabled depending on workflow step)

### Settings popover (⚙️)

Top-right is the **⚙️ Settings** popover. It contains:

- Run metadata (Project ID / Run ID / Latest version)
- **Refresh run** (reloads run state from the backend)
- **Versions (view only)**: select a version number to view the stored content
- **Load run** form: load a run by Project ID + Run ID

---

## 3) Workflow: Generate a run

1. In the chat area, choose a **persona** (when no run is loaded):
   - `taylor_swift`
   - `bbc`

2. In the chat input, type a topic and press **Enter**.

What to expect:

- Your message should appear **immediately** in the chat.
- The UI will show a status spinner while generating.
- When complete, the assistant draft is added to the chat.

After generation completes:

- The chat input is **disabled** until you request a review.

---

## 4) Request a review

In the assistant’s latest draft message bubble, click:

**Request review**

What to expect:

- Input stays **disabled** while the review runs.
- When finished, a review section appears below the chat with:
  - Fidelity score
  - A list of violations (each with a checkbox)

---

## 5) Select violations and rewrite

1. Tick one or more violation checkboxes.

2. Once at least one is selected, the chat input becomes enabled for:

**Rewrite comments (press Enter to submit)**

3. Type your rewrite instructions and press **Enter**.

What to expect:

- Your rewrite comments appear immediately in the chat.
- The UI locks input while rewriting.
- When complete, a new version is appended on the backend and the new draft appears.

After rewrite completes:

- Input is disabled again until you click **Request review** for the latest version.

---

## 6) View older versions (read-only)

Open ⚙️ **Settings** → **Versions (view only)**:

- Select the version number
- The content will be displayed in a code block

This version browser is **view-only** and does not affect the active chat messages.

---

## 7) Load an existing run

Open ⚙️ **Settings** → **Load run**:

1. Enter the Project ID and Run ID
2. Click **Load run**

This reloads the run state from disk via the backend and refreshes the UI.

---

## Notes / troubleshooting

- If the UI seems out of sync with the backend, use **⚙️ Settings → Refresh run**.
- If you restart the backend, you may need to refresh/reload a run in the UI.
- Runs are persisted under `db/` as JSON.
