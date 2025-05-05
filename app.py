import streamlit as st

st.set_page_config(page_title="ANE English Medical Note Taker", layout="centered")
from db.models import setup_database, get_session_details_by_index
from ui.session_ui import (
    session_interaction,
    _parse_structured_summary,
    _combine_structured_summary,
    SUMMARY_LABELS_EN,  # Updated
)
from ui.login_ui import login_flow
from utils.helpers import export_summary_pdf
from ui.job_manager import render_sidebar


setup_database()

if not login_flow():
    st.warning("⚠️ Please log in first.")
    st.stop()

render_sidebar()
st.title("📋 Emergency Medical Note Taker (ANE) - Arabic")

# Navigation
view_choice = st.sidebar.radio(
    "Go to:",
    ("New Session", "📂 Past Sessions"),
    key="view_choice",  # ★ bind to session_state
)
# ----------------- Page: New Session ------------------
if view_choice == "New Session":

    def reset_session_state_for_new_session():
        keys_to_clear = [
            "wizard_step",
            "doctor_name",
            "patient_name",
            "date_selected",
            "audio_bytes",
            "audio_file_path",
            "transcript",
            "summary_raw",
            "analysis_ready",
            "keywords",
            "diagnoses",
            "new_session",
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)

    if st.sidebar.button("🔁 Start New Session"):
        reset_session_state_for_new_session()
        st.session_state["new_session"] = True
        st.rerun()

    if st.session_state.get("new_session"):
        session_interaction()

# ----------------- Page: Past Sessions ------------------
elif view_choice == "📂 Past Sessions":
    st.header("📂 Previous Sessions")

    all_sessions = get_session_details_by_index(st.session_state.user_id)
    preset = None
    target_id = st.session_state.pop("selected_past_session_id", None)
    if target_id is not None:
        for i, row in enumerate(all_sessions):
            if row[0] == target_id:  # row[0] is session_id
                preset = i
                break
    if not all_sessions:
        st.info("No saved sessions found.")
        st.stop()

    session_labels = [
        f"{row[1].strftime('%Y-%m-%d')} – 👨‍⚕️ {row[2]} | 👤 {row[3]}"
        for row in all_sessions
    ]
    selected_idx = st.selectbox(
        "Select a previous session:",
        range(len(session_labels)),
        index=preset or 0,
        format_func=lambda i: session_labels[i],
    )

    session_id, date_sel, doctor_name, patient_name, transcript, summary = all_sessions[
        selected_idx
    ]

    st.subheader("📄 Full Transcript")
    st.write(transcript)

    st.subheader("📝 Session Summary")
    sections = _parse_structured_summary(summary)
    updated: dict[str, str] = {}
    for lbl in SUMMARY_LABELS_EN:
        key = f"past_summary_{lbl}"
        updated[lbl] = st.text_area(
            lbl + ":", value=sections.get(lbl, ""), key=key, height=90
        )

    if st.button("📄 Generate / Refresh PDF", key="past_pdf_btn"):
        combined = _combine_structured_summary(updated)
        pdf_path = export_summary_pdf(
            doctor_name, patient_name, date_sel, combined, transcript
        )
        st.session_state["past_pdf_path"] = pdf_path
        st.success("PDF ready – download below or send by e-mail.")
        st.rerun()

    if pdf_path := st.session_state.get("past_pdf_path"):
        col_dl, col_mail = st.columns(2)

        # 1️⃣  Download
        with col_dl, open(pdf_path, "rb") as fp:
            st.download_button(
                "📥 Download Summary",
                fp,
                file_name="summary.pdf",
                key="download_btn",
            )

        # 2️⃣  E-mail
        with col_mail:
            default_email = st.session_state.get(
                "user_email"
            ) or st.session_state.get(  # set at login
                "user_name", ""
            )
            to_addr = st.text_input(
                "✉️ Send to (email)",
                value=default_email,
                key="past_send_to_email",
            )
            btn_disabled = not to_addr.strip()
            if st.button("📧 Email PDF", disabled=btn_disabled, key="past_email_btn"):
                from utils.email_utils import send_pdf

                try:
                    send_pdf(
                        to_email=to_addr,
                        pdf_path=pdf_path,
                        subject="Medical Session Summary",
                        body="Attached is the PDF summary you requested.",
                    )
                    st.success(f"Sent to {to_addr}")
                except RuntimeError as e:
                    st.error(str(e))
