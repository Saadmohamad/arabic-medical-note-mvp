import streamlit as st

st.set_page_config(page_title="ANE English Medical Note Taker", layout="centered")

from db.models import setup_database
from ui.login_ui import login_flow
from ui.session_ui import session_interaction

# DB init
setup_database()

# --- Authentication ---
if not login_flow():
    st.warning("⚠️ Please log in first.")
    st.stop()


# --- New session only ---
def reset_session_state_for_new_session():
    keys_to_clear = [
        "doctor_name",
        "patient_name",
        "date_selected",
        "audio_file",  # <- if using this for Streamlit audio_input
        "audio_bytes",  # <- if storing raw bytes
        "audio_file_path",
        "transcript",
        "summary_raw",
        "analysis_ready",
        "keywords",
        "diagnoses",
        "new_session_pdf_path",
        "pdf_ready",
        "result",
        "send_to_email",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


st.sidebar.button("🔁 Start New Session", on_click=reset_session_state_for_new_session)
session_interaction()
