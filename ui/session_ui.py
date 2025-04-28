from __future__ import annotations
import datetime
import re
import gc
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

import streamlit as st

try:
    from st_audiorec import st_audiorec
except ModuleNotFoundError:  # pragma: no cover
    st.error(
        "❗ `streamlit-audiorec` not installed. Run `pip install streamlit-audiorec`."
    )
    st.stop()

from nlp.transcribe import transcribe_audio as _transcribe_audio
from nlp.summarise import summarize_transcript
from nlp.analyse import extract_symptom_keywords, extract_possible_diagnoses

from db.models import insert_doctor, insert_patient, insert_session
from utils.helpers import export_summary_pdf
from utils.audio_io import bytes_to_wav
from utils.secret import get as _secret

__all__ = ["session_interaction"]

SUMMARY_LABELS_EN = [
    "Patient Complaint",
    "Clinical Notes",
    "Diagnosis (if any)",
    "Treatment Plan",
]


# -----------------------------------------------------------------------------
# 🔊  Caching layers -----------------------------------------------------------
# -----------------------------------------------------------------------------


@st.cache_data(show_spinner="🔊 Transcribing…")
def transcribe_file(path: str) -> str:
    return _transcribe_audio(path)


@st.cache_data(show_spinner="📝 Summarising…")
def summarise_cached(transcript: str) -> str:
    """One‑hour cache for GPT summary; key = transcript hash."""
    return summarize_transcript(transcript)


@st.cache_data(show_spinner="🔍 Extracting symptoms…")
def extract_symptoms_cached(summary: str, transcript: str) -> str:
    return extract_symptom_keywords(summary, transcript)


@st.cache_data(show_spinner="🩺 Generating differential…")
def extract_diagnoses_cached(summary: str, transcript: str) -> str:
    return extract_possible_diagnoses(summary, transcript)


# -----------------------------------------------------------------------------
# ✉️  Email helper -------------------------------------------------------------
# -----------------------------------------------------------------------------


def _send_email(pdf_path: str, recipient: str) -> None:
    """Send *pdf_path* as an attachment to *recipient* using SMTP creds in *st.secrets*."""

    host = _secret("SMTP_HOST")
    port = int(_secret("SMTP_PORT", default="587"))
    user = _secret("SMTP_USER")
    pwd = _secret("SMTP_PASS")

    msg = EmailMessage()
    msg["Subject"] = "Session Summary PDF"
    msg["From"] = user
    msg["To"] = recipient
    msg.set_content("Attached is your medical session summary.")

    with open(pdf_path, "rb") as fp:
        msg.add_attachment(
            fp.read(),
            maintype="application",
            subtype="pdf",
            filename="summary.pdf",
        )

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)


# -----------------------------------------------------------------------------
# 🖼️  Layout helpers -----------------------------------------------------------
# -----------------------------------------------------------------------------


def _inject_ltr_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stAppViewContainer"] {direction:ltr;text-align:left;}
        section[data-testid="stSidebar"],div[data-testid="stSidebar"] {
            direction:ltr;text-align:left;position:fixed;left:0;right:auto;}
        [data-testid="stSidebar"] * {direction:ltr;text-align:left;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _clean_line(line: str) -> str:
    return re.sub(r"^[\s\-•]+", "", line).strip()


def _parse_structured_summary(text: str) -> dict[str, str]:
    sections: dict[str, str] = {lbl: "" for lbl in SUMMARY_LABELS_EN}
    current: Optional[str] = None
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


# -----------------------------------------------------------------------------
# 🧑‍⚕️  Main multi‑step wizard --------------------------------------------------
# -----------------------------------------------------------------------------


def session_interaction() -> None:
    """Interactive wizard for recording and processing a medical session."""

    _inject_ltr_css()

    # Initialise wizard step
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1

    # ------------------------------------------------------------------
    # Step 1 – Meta data
    # ------------------------------------------------------------------
    if st.session_state.wizard_step == 1:
        st.subheader("🩺 Doctor & Patient Details")

        with st.form("meta", clear_on_submit=False):
            doctor_name = st.text_input("👨‍⚕️ Doctor's Name")
            patient_name = st.text_input("👤 Patient Name")
            date_sel = st.date_input("📅 Date", value=datetime.date.today())
            next_clicked = st.form_submit_button("Next ➡️", use_container_width=True)

        if next_clicked:
            if not doctor_name.strip():
                st.error("Please enter the doctor's name before continuing.")
            elif not patient_name.strip():
                st.error("Please enter the patient's name before continuing.")
            else:
                st.session_state.update(
                    {
                        "doctor_name": doctor_name.strip(),
                        "patient_name": patient_name.strip(),
                        "date_selected": date_sel,
                        "wizard_step": 2,
                    }
                )
                st.rerun()
        return

    # ------------------------------------------------------------------
    # Step 2 – Record audio
    # ------------------------------------------------------------------
    if st.session_state.wizard_step == 2:
        st.subheader("🎙️ Record Session")
        status = st.empty()
        bytes_rec = st_audiorec()

        if bytes_rec is None:
            status.markdown(
                "<span style='color:red;font-size:24px;animation:blinker 1s infinite'>●</span> Recording…",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<style>@keyframes blinker{50%{opacity:0}}</style>",
                unsafe_allow_html=True,
            )
        else:
            status.success("Recording complete ✔️")

        if bytes_rec:
            st.session_state.audio_file_path = bytes_to_wav(bytes_rec)
            del bytes_rec
            gc.collect()

        st.button(
            "Next ➡️",
            disabled="audio_file_path" not in st.session_state,
            on_click=lambda: st.session_state.update({"wizard_step": 3}),
        )
        return

    # ------------------------------------------------------------------
    # Step 3 – Process & summarise
    # ------------------------------------------------------------------
    if st.session_state.wizard_step == 3:
        st.subheader("📤 Process Audio")
        audio_path: str = st.session_state.audio_file_path  # type: ignore[arg-type]

        # -- Transcribe
        if "transcript" not in st.session_state:
            with st.status("Transcribing…", expanded=False):
                st.session_state.transcript = transcribe_file(audio_path)

        # -- Summarise
        if "summary_raw" not in st.session_state:
            with st.status("Summarising…", expanded=False):
                st.session_state.summary_raw = summarise_cached(
                    st.session_state.transcript
                )

        # -- AI analysis
        if not st.session_state.get("analysis_ready"):
            with st.spinner("Running AI analysis…"):
                st.session_state.keywords = extract_symptoms_cached(
                    st.session_state.summary_raw, st.session_state.transcript
                )
                st.session_state.diagnoses = extract_diagnoses_cached(
                    st.session_state.summary_raw, st.session_state.transcript
                )
                st.session_state.analysis_ready = True

            # Persist session to DB
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
            try:
                Path(audio_path).unlink(missing_ok=True)
            except Exception:
                pass

        # -- Display transcript
        st.markdown("### 📄 Full Transcript")
        st.write(st.session_state.transcript)

        # ------------------------------------------------------------
        # 📝 Summary editing UI
        # ------------------------------------------------------------
        st.markdown("### 📝 Edit Summary")
        st.info("The fields below are AI-generated. You may edit them as needed.")

        sections = _parse_structured_summary(st.session_state.summary_raw)
        sections["Clinical Notes"] += "\nSymptoms: " + st.session_state.keywords
        sections["Diagnosis (if any)"] = st.session_state.diagnoses

        updated: dict[str, str] = {}
        for lbl in SUMMARY_LABELS_EN:
            updated[lbl] = st.text_area(
                f"{lbl}:", value=sections.get(lbl, ""), key=f"summary_{lbl}", height=90
            )

        # ------------------------------------------------------------
        # 📄 Generate / download / email PDF
        # ------------------------------------------------------------
        if st.button("📄 Generate Summary PDF"):
            combined = _combine_structured_summary(updated)
            pdf_path = export_summary_pdf(
                st.session_state.doctor_name,
                st.session_state.patient_name,
                st.session_state.date_selected,
                combined,
                st.session_state.transcript,
            )
            st.session_state.latest_pdf = pdf_path
            st.success("PDF is ready – download or send via email below.")
            st.rerun()

        # Show actions if a PDF exists
        print(st.session_state.get("latest_pdf"))
        if pdf_path := st.session_state.get("latest_pdf"):
            with open(pdf_path, "rb") as fp:
                st.download_button("📥 Download Summary", fp, file_name="summary.pdf")

            recipient = st.text_input("✉️ Recipient Email", key="recipient_email")
            send_clicked = st.button(
                "Send Email", key="send_email_btn", disabled=not recipient
            )

            if send_clicked and recipient:
                try:
                    _send_email(pdf_path, recipient)
                    st.success(f"Summary emailed to {recipient} ✔️")
                    # Optionally delete PDF after sending
                    Path(pdf_path).unlink(missing_ok=True)
                    del st.session_state.latest_pdf
                except Exception as exc:
                    st.error(f"Failed to send email: {exc}")

        return
