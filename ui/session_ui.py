from __future__ import annotations
import datetime
import tempfile
import re
import streamlit as st

try:
    from st_audiorec import st_audiorec
except ModuleNotFoundError:
    st.error(
        "❗ `streamlit-audiorec` not installed. Run `pip install streamlit-audiorec`."
    )
    st.stop()

from nlp.transcribe import transcribe_audio
from nlp.summarise import summarize_transcript
from nlp.analyse import extract_symptom_keywords, extract_possible_diagnoses
from db.models import insert_doctor, insert_patient, insert_session, get_patient_names
from utils.helpers import export_summary_pdf

__all__ = ["session_interaction"]

SUMMARY_LABELS_EN = [
    "Patient Complaint",
    "Clinical Notes",
    "Diagnosis (if any)",
    "Treatment Plan",
]


def _inject_ltr_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stAppViewContainer"] {
            direction: ltr !important;
            text-align: left !important;
        }
        section[data-testid="stSidebar"], div[data-testid="stSidebar"] {
            direction: ltr !important;
            text-align: left !important;
            position: fixed !important;
            left: 0 !important;
            right: auto !important;
        }
        [data-testid="stSidebar"] * {
            direction: ltr !important;
            text-align: left !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _clean_line(line: str) -> str:
    return re.sub(r"^[\s\-•]+", "", line).strip()


def _parse_structured_summary(text: str) -> dict[str, str]:
    sections: dict[str, str] = {lbl: "" for lbl in SUMMARY_LABELS_EN}
    current: str | None = None
    for raw in text.splitlines():
        line = _clean_line(raw)
        for lbl in SUMMARY_LABELS_EN:
            if line.startswith(lbl):
                current = lbl
                parts = line.split(":", 1)
                sections[current] = parts[1].strip() if len(parts) > 1 else ""
                break
        else:
            if current:
                sections[current] += " " + line
    return sections


def _combine_structured_summary(sections: dict[str, str]) -> str:
    return "\n".join(f"- {lbl}: {val.strip()}" for lbl, val in sections.items())


def session_interaction() -> None:
    _inject_ltr_css()

    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1

    # Step 1: Identify doctor & patient
    if st.session_state.wizard_step == 1:
        st.subheader("🩺 Doctor & Patient Details")
        doctor_name = st.text_input("👨‍⚕️ Doctor's Name")
        patient_sel = st.selectbox(
            "🧑‍🤝‍🧑 Select Patient", options=[""] + get_patient_names()
        )
        if not patient_sel:
            patient_sel = st.text_input("Or enter a new patient name")
        date_sel = st.date_input("📅 Date", value=datetime.date.today())
        if st.button("Next ➡️", disabled=not doctor_name):
            st.session_state.update(
                {
                    "doctor_name": doctor_name,
                    "patient_name": patient_sel,
                    "date_selected": date_sel,
                    "wizard_step": 2,
                }
            )
            st.rerun()
        return

    # Step 2: Record audio
    if st.session_state.wizard_step == 2:
        st.subheader("🎙️ Record Session")
        status = st.empty()
        bytes_rec = st_audiorec()
        if bytes_rec is None:
            status.markdown(
                "<span style='color:red;font-size:24px;animation:blinker 1s infinite'>●</span> Recording...",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<style>@keyframes blinker{50%{opacity:0}}</style>",
                unsafe_allow_html=True,
            )
        else:
            status.success("Recording complete ✔️")
        if bytes_rec and st.session_state.get("audio_bytes") != bytes_rec:
            st.session_state.audio_bytes = bytes_rec
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(bytes_rec)
                st.session_state.audio_file_path = tmp.name
        st.button(
            "Next ➡️",
            disabled="audio_file_path" not in st.session_state,
            on_click=lambda: st.session_state.update({"wizard_step": 3}),
        )
        return

    # Step 3: Process and summarize
    if st.session_state.wizard_step == 3:
        st.subheader("📤 Process Audio")
        audio_path: str = st.session_state.audio_file_path  # type: ignore

        if "transcript" not in st.session_state:
            with st.status("Transcribing…", expanded=False):
                st.session_state.transcript = transcribe_audio(audio_path)

        if "summary_raw" not in st.session_state:
            with st.status("Summarizing…", expanded=False):
                st.session_state.summary_raw = summarize_transcript(
                    st.session_state.transcript
                )

        if not st.session_state.get("analysis_ready"):
            with st.spinner("Running AI analysis…"):
                st.session_state.keywords = extract_symptom_keywords(
                    st.session_state.summary_raw, st.session_state.transcript
                )
                st.session_state.diagnoses = extract_possible_diagnoses(
                    st.session_state.summary_raw, st.session_state.transcript
                )
                st.session_state.analysis_ready = True

            doc_id = insert_doctor(st.session_state.doctor_name)
            pat_id = insert_patient(st.session_state.patient_name)
            insert_session(
                st.session_state.user_id,
                doc_id,
                pat_id,
                st.session_state.date_selected,
                st.session_state.transcript,
                st.session_state.summary_raw,
                audio_path,
            )
            st.success("✅ Session saved!")

        st.markdown("### 📄 Full Transcript")
        st.write(st.session_state.transcript)

        st.markdown("### 📝 Edit Summary")
        st.info("The fields below are AI-generated. You may edit them as needed.")

        sections = _parse_structured_summary(st.session_state.summary_raw)
        sections["Clinical Notes"] += "\nSymptoms: " + st.session_state.keywords
        sections["Diagnosis (if any)"] = st.session_state.diagnoses

        updated: dict[str, str] = {}
        for lbl in SUMMARY_LABELS_EN:
            key = f"summary_{lbl}"
            updated[lbl] = st.text_area(
                f"{lbl}:", value=sections.get(lbl, ""), key=key, height=90
            )

        if st.button("📄 Export PDF"):
            combined = _combine_structured_summary(updated)
            pdf_path = export_summary_pdf(
                st.session_state.doctor_name,
                st.session_state.patient_name,
                st.session_state.date_selected,
                combined,
                st.session_state.transcript,
            )
            with open(pdf_path, "rb") as fp:
                st.download_button("📥 Download Summary", fp, file_name="summary.pdf")
        return
