# ui/session_ui.py
from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional
import streamlit as st
from utils.audio_io import bytes_to_wav
from utils.async_tasks import process_session_sync
from utils.helpers import export_summary_pdf

# ────────────────────────────────────────────────────────────── Constants
SUMMARY_LABELS_EN: List[str] = [
    "Patient Complaint",
    "Clinical Notes",
    "Diagnosis",
    "Treatment Plan",
]
NO_DATA = "No available readout"

# ────────────────────────────────────────────────────────────── UI helpers


def _inject_custom_css() -> None:
    """Force L-to-R layout even when Arabic text appears."""
    st.markdown(
        """
        <style>
            div[data-testid=\"stAppViewContainer\"]{direction:ltr;text-align:left;}
            section[data-testid=\"stSidebar\"],div[data-testid=\"stSidebar\"]{
                direction:ltr;text-align:left;position:fixed;left:0;right:auto;}
            [data-testid=\"stSidebar\"] *{direction:ltr;text-align:left;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_structured_summary(raw: str | Dict[str, Any] | List[str]) -> Dict[str, str]:
    result: Dict[str, str] = {k: NO_DATA for k in SUMMARY_LABELS_EN}
    if isinstance(raw, dict):
        data = raw
    else:
        try:
            data = json.loads(raw) if isinstance(raw, str) else {}
        except json.JSONDecodeError:
            data = {}
    if isinstance(data, dict):
        for k in SUMMARY_LABELS_EN:
            v = data.get(k, "")
            if isinstance(v, list):
                v = "\n".join(v)
            text = str(v).strip()
            result[k] = text if text else NO_DATA
        return result
    lines: List[str] = []
    if isinstance(raw, list):
        for item in raw:
            lines.extend(str(item).splitlines())
    else:
        lines = str(raw).splitlines()
    current: Optional[str] = None
    for line in lines:
        text = line.lstrip(" -•").strip()
        if ":" in text:
            head, tail = text.split(":", 1)
            head = head.strip()
            if head in SUMMARY_LABELS_EN:
                current = head
                result[head] = tail.strip() or NO_DATA
                continue
        if current:
            prev = result[current]
            addition = text
            result[current] = addition if prev == NO_DATA else prev + "\n" + addition
    return result


# ───────────────────────────────────────────────────────────── Main UI


def session_interaction() -> None:
    _inject_custom_css()
    st.title("📋 Emergency Medical Note Taker (ANE) - Arabic")
    st.subheader("🩺 Doctor & Patient Details + Recording")

    with st.form("session_form", clear_on_submit=False):
        doctor_name = st.text_input("👨‍⚕️ Doctor's Name")
        patient_name = st.text_input("👤 Patient Name")
        date_sel = st.date_input("📅 Date", value=datetime.date.today())
        audio_file = st.audio_input("Click to record ▶️")
        submitted = st.form_submit_button("▶️ Start Processing", type="primary")

    if submitted:
        if not doctor_name.strip() or not patient_name.strip() or audio_file is None:
            st.error(
                "Please complete all fields and record a session before processing."
            )
            return

        wav_path = bytes_to_wav(audio_file.getvalue())

        with st.spinner("⏳ Processing: transcribing & summarizing..."):
            payload: Dict[str, Any] = {
                "doctor_name": doctor_name.strip(),
                "patient_name": patient_name.strip(),
                "date_selected": date_sel,
                "audio_path": wav_path,
                "user_id": st.session_state.get("user_id"),
            }
            result = process_session_sync(payload)

        if err := result.get("pipeline_error"):
            st.error(f"🚨 {err}")
            return

        # Save everything into session_state
        st.session_state["result"] = result
        st.session_state["doctor_name"] = doctor_name
        st.session_state["patient_name"] = patient_name
        st.session_state["date_selected"] = date_sel

    # If we have result stored, continue rendering
    if "result" not in st.session_state:
        return

    result = st.session_state["result"]
    doctor_name = st.session_state["doctor_name"]
    patient_name = st.session_state["patient_name"]
    date_sel = st.session_state["date_selected"]

    st.subheader("📄 Full Transcript")
    st.write(result["transcript"])

    st.markdown("### 📝 Edit Summary")
    sections = _parse_structured_summary(result.get("summary_raw", ""))
    updated: Dict[str, str] = {}
    for lbl in SUMMARY_LABELS_EN:
        updated[lbl] = st.text_area(f"{lbl}:", value=sections.get(lbl, ""), height=90)

    if st.button("📄 Generate Summary PDF", key="generate_pdf_btn"):
        pdf_path = export_summary_pdf(
            doctor_name,
            patient_name,
            date_sel,
            updated,
            result["transcript"],
        )
        st.session_state["new_session_pdf_path"] = pdf_path
        st.session_state["pdf_ready"] = True
        st.success("✅ PDF ready – download below or send by email.")

    # Show download/email if ready
    if st.session_state.get("pdf_ready") and st.session_state.get(
        "new_session_pdf_path"
    ):
        pdf_path = st.session_state["new_session_pdf_path"]
        with open(pdf_path, "rb") as fp:
            pdf_bytes = fp.read()

        dl_col, mail_col = st.columns(2)
        with dl_col:
            st.download_button(
                "📥 Download Summary",
                data=pdf_bytes,
                file_name="summary.pdf",
                key="download_summary",
            )

        with mail_col:
            default_email = st.session_state.get("user_name", "")
            to_addr = st.text_input(
                "✉️ Send to (email)", value=default_email, key="send_to_email"
            )
            if st.button("📧 Email PDF", disabled=not to_addr.strip(), key="email_pdf"):
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
