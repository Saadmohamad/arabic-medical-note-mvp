"""Session interaction module
Uses **streamlit‑audiorec** (st_audiorec) for recording with a single
built‑in playback element. Adds an explicit **Reset** button and removes
the extra `st.audio()` call that caused duplicate players.
"""

from __future__ import annotations

import datetime
import tempfile
import streamlit as st

try:
    from st_audiorec import st_audiorec  # pip install streamlit-audiorec
except ModuleNotFoundError:
    st.error(
        "❗ `streamlit-audiorec` component not found. Run `pip install streamlit-audiorec` and restart the app."
    )
    st.stop()

from nlp.transcribe import transcribe_audio
from nlp.summarise import summarize_transcript
from nlp.analyse import (
    extract_symptom_keywords,
    extract_possible_diagnoses,
)
from db.models import (
    insert_doctor,
    insert_patient,
    insert_session,
    get_patient_names,
)
from utils.helpers import export_summary_pdf

__all__ = ["session_interaction"]

# -----------------------------------------------------------------------------
# 🩺  Main entry point rendered from app.py
# -----------------------------------------------------------------------------

def session_interaction() -> None:
    """End‑to‑end UI flow for a single doctor–patient session."""

    # ------------------------------------------------------------------
    # 1 ▸ Doctor / patient metadata
    # ------------------------------------------------------------------
    st.subheader("🩺 Identify Doctor & Start Session")

    doctor_name: str = st.text_input("👨‍⚕️ Doctor Name (in Arabic)")

    patient_names = get_patient_names()
    patient_name: str = st.selectbox(
        "🧑‍🤝‍🧑 Select Patient", options=["" ] + patient_names
    )
    if not patient_name:
        patient_name = st.text_input("Or enter new patient name (in Arabic)")

    date: datetime.date = st.date_input("📅 Date", value=datetime.date.today())

    # ------------------------------------------------------------------
    # 2 ▸ Audio recording block (st_audiorec)
    # ------------------------------------------------------------------
    st.markdown("### 🎙️ Record Session Audio")
    st.info("Click the microphone **once** to start recording and **again** to stop.")

    if "audio_bytes" not in st.session_state:
        st.session_state.audio_bytes: bytes | None = None
        st.session_state.audio_file_path: str | None = None

    # st_audiorec handles start/stop & playback. No extra st.audio() call here.
    audio_bytes: bytes | None = st_audiorec()

    # Save recording once completed
    if audio_bytes is not None and audio_bytes != st.session_state.get("audio_bytes"):
        st.session_state.audio_bytes = audio_bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            st.session_state.audio_file_path = tmp.name



    # ------------------------------------------------------------------
    # 3 ▸ Process, summarise, and analyse
    # ------------------------------------------------------------------
    if st.button("📤 Process & Summarize"):
        missing_fields = [
            name
            for name, value in {
                "Doctor name": doctor_name,
                "Patient name": patient_name,
                "Audio recording": st.session_state.get("audio_file_path"),
            }.items()
            if not value
        ]

        if missing_fields:
            st.error("❗ Please provide: " + ", ".join(missing_fields))
            return

        audio_path = st.session_state.audio_file_path  # type: ignore[str-bytes-safe]

        # --------------------------- Whisper → transcript -------------------
        with st.spinner("Transcribing audio…"):
            transcript: str = transcribe_audio(audio_path)

        # --------------------------- GPT → summary -------------------------
        with st.spinner("Generating summary…"):
            summary: str = summarize_transcript(transcript)

        # --------------------------- DB persistence ------------------------
        doctor_id = insert_doctor(doctor_name)
        patient_id = insert_patient(patient_name)
        insert_session(doctor_id, patient_id, date, transcript, summary, audio_path)

        st.success("✅ Session processed and saved!")

        # --------------------------- Editable summary ----------------------
        st.markdown("### 📝 Editable Summary")
        updated_summary = st.text_area("Edit Summary:", value=summary, height=240)

        # --------------------------- PDF export ----------------------------
        if st.button("📄 Export PDF"):
            pdf_path = export_summary_pdf(
                doctor_name, patient_name, date, updated_summary
            )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📥 Download Summary as PDF",
                    f,
                    file_name="summary.pdf",
                )

        st.markdown("---")
        st.markdown("### 📄 Transcript")
        st.write(transcript)

        # --------------------------- Analytics -----------------------------
        if st.button("📊 Analyze Session"):
            st.markdown("## 🔍 Session Analytics")

            keywords = extract_symptom_keywords(updated_summary, transcript)
            st.markdown(f"**🧠 Extracted Symptom Keywords:**\n\n{keywords}")

            diagnoses = extract_possible_diagnoses(updated_summary, transcript)
            st.markdown(f"**📈 Possible Diagnoses:**\n\n{diagnoses}")
