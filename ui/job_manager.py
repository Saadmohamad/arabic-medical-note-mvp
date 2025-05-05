# ui/job_manager.py
from __future__ import annotations

import datetime
import uuid
from concurrent.futures import Future
import streamlit as st

# ---------------------------------------------------------------------------
# Internal helpers / aliases
# ---------------------------------------------------------------------------
JobStatus = dict[str, str | Future | datetime.datetime]


def _init() -> None:
    """Ensure the jobs dict exists inside session_state."""
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def add_job(fut: Future, *, meta: dict[str, str]) -> str:
    """
    Register a background Future and return its job-id (8-char hex).

    Parameters
    ----------
    fut  : concurrent.futures.Future
        The Future returned by `enqueue_job(...)`.
    meta : dict[str, str]
        Extra fields to display in the sidebar (e.g. patient, doctor, date).
    """
    _init()
    jid = uuid.uuid4().hex[:8]
    st.session_state.jobs[jid] = {
        "future": fut,
        "status": "⏳ pending",
        "submitted": datetime.datetime.now(),
        **meta,
    }
    return jid


def refresh_jobs() -> None:
    """Update each stored job’s status in-place."""
    _init()
    for job in st.session_state.jobs.values():
        fut: Future = job["future"]  # type: ignore
        if fut.done():
            if fut.exception():
                job["status"] = "❌ error"
            else:
                job["status"] = "✅ done"
                res = fut.result()
                # If the pipeline returned a session_id, copy it for “View result”
                if res and "session_id" in res:
                    job["session_id"] = res["session_id"]


def render_sidebar() -> None:
    """
    Call once (e.g. from app.py) to draw the background-jobs section
    in the Streamlit sidebar.
    """
    refresh_jobs()
    jobs = st.session_state.jobs
    if not jobs:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Background jobs")

    for jid, job in list(jobs.items()):
        label = f"{job.get('patient', '') or job.get('title', 'Job')} – {job['status']}"
        with st.sidebar.expander(label, expanded=False):
            st.write(f"**ID:** `{jid}`")
            st.write(f"**Started:** {job['submitted'].strftime('%H:%M:%S')}")
            if job["status"].startswith("✅") and job.get("session_id"):
                if st.button("View result", key=f"view_{jid}"):
                    st.session_state["view_choice"] = "📂 Past Sessions"
                    st.session_state["selected_past_session_id"] = job["session_id"]
                    st.rerun()

            if st.button("🗑️ Remove", key=f"del_{jid}"):
                jobs.pop(jid, None)
                st.rerun()
