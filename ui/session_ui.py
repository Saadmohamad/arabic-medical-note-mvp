# ui/session_ui.py
from __future__ import annotations

import datetime
import json
import tempfile
import wave
from enum import IntEnum
from typing import Any, Dict, Optional, Union

import numpy as np
import streamlit as st
from st_audiorec import st_audiorec
from ui.job_manager import add_job
from utils.audio_io import bytes_to_wav
from utils.async_tasks import enqueue_job
from utils.helpers import export_summary_pdf


# ──────────────────────────────────────────────────────────────── Wizard steps
class Step(IntEnum):
    META = 1
    RECORD = 2
    READY = 3
    PROCESSING = 4
    RESULTS = 5


# ────────────────────────────────────────────────────────────────── Constants
SUMMARY_LABELS_EN = [
    "Patient Complaint",
    "Clinical Notes",
    "Diagnosis",
    "Treatment Plan",
]

NO_DATA = "No available readout"  # used by _parse_structured_summary


# ──────────────────────────────────────────────────────────────── UI helpers
def _inject_custom_css() -> None:
    """Force L-to-R layout even when Arabic text appears."""
    st.markdown(
        """
        <style>
            div[data-testid="stAppViewContainer"]{direction:ltr;text-align:left;}
            section[data-testid="stSidebar"],div[data-testid="stSidebar"]{
                direction:ltr;text-align:left;position:fixed;left:0;right:auto;}
            [data-testid="stSidebar"] *{direction:ltr;text-align:left;}
        </style>
        """,
        unsafe_allow_html=True,
    )


NO_DATA = "No inputs available"  # <-- updated placeholder


def _parse_structured_summary(raw: str | dict) -> Dict[str, str]:
    """
    Accept JSON-string/dict or bullet-list, return dict with placeholder if empty.
    """
    result: Dict[str, str] = {k: NO_DATA for k in SUMMARY_LABELS_EN}

    # JSON / dict parsing
    if isinstance(raw, dict):
        for k in SUMMARY_LABELS_EN:
            val = raw.get(k, "").strip()
            result[k] = val if val else NO_DATA
        return result

    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            for k in SUMMARY_LABELS_EN:
                val = obj.get(k, "").strip()
                result[k] = val if val else NO_DATA
            return result
    except (TypeError, ValueError, json.JSONDecodeError):
        pass  # fall through to legacy parsing

    # Legacy bullet-list parsing
    current: Optional[str] = None
    for line in str(raw).splitlines():
        line = line.lstrip(" -•").strip()
        if ":" in line:
            head, tail = line.split(":", 1)
            head = head.strip()
            if head in SUMMARY_LABELS_EN:
                current = head
                val = tail.strip()
                result[head] = val if val else NO_DATA
                continue
        if current:
            if result[current] == NO_DATA:
                result[current] = line
            else:
                result[current] += " " + line

    return result


def _combine_structured_summary(sections: Dict[str, str]) -> str:
    """Re-serialise the dict back into the simple bullet list used in PDFs/DB."""
    return "\n".join(f"- {k}: {v.strip()}" for k, v in sections.items())


# ───────────────────────────────────────────────────────────── Audio helpers
def _np_float_to_wav(samples: np.ndarray, *, sr: int = 48_000) -> str:
    """Convert a float32 NumPy array (-1.0…1.0) to a 16-bit PCM mono WAV file."""
    pcm16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16)
    return tmp.name


# ────────────────────────────────────────────────────────────── Main wizard
def session_interaction() -> None:
    """Entry-point called from `app.py` when the user starts a new session."""
    _inject_custom_css()

    # Initialise wizard state once
    st.session_state.setdefault("wizard_step", Step.META)

    # ─────────────────────────────── 1️⃣  Meta-data page
    if st.session_state.wizard_step == Step.META:
        st.subheader("🩺 Doctor & Patient Details")
        with st.form("meta"):
            doctor_name = st.text_input("👨‍⚕️ Doctor's Name")
            patient_name = st.text_input("👤 Patient Name")
            date_sel = st.date_input("📅 Date", value=datetime.date.today())
            if st.form_submit_button("Next ➡️", use_container_width=True):
                if not doctor_name.strip() or not patient_name.strip():
                    st.error("Please complete all fields before continuing.")
                else:
                    st.session_state.update(
                        doctor_name=doctor_name.strip(),
                        patient_name=patient_name.strip(),
                        date_selected=date_sel,
                        wizard_step=Step.RECORD,
                    )
                    st.rerun()
        return

    # ─────────────────────────────── 2️⃣  Audio recording page
    if st.session_state.wizard_step == Step.RECORD:
        st.subheader("🎙️ Record Session")
        raw_audio: Union[bytes, np.ndarray, None] = st_audiorec()

        # No audio yet ➜ show instructions
        if (
            raw_audio is None
            or (isinstance(raw_audio, bytes) and not raw_audio)
            or (isinstance(raw_audio, np.ndarray) and raw_audio.size == 0)
        ):
            st.info("Click the mic icon, speak, then press stop to finish.")
            return

        # Convert to WAV (bytes → tmp file OR ndarray → tmp file)
        wav_path = (
            bytes_to_wav(raw_audio)
            if isinstance(raw_audio, bytes)
            else _np_float_to_wav(raw_audio)
        )

        st.session_state.update(wav_path=wav_path, wizard_step=Step.READY)
        st.rerun()
        return

    # ─────────────────────────────── 3️⃣  Post-record (download/process)
    if st.session_state.wizard_step == Step.READY:
        st.subheader("🎧 Recording Ready")

        # playback widget
        with open(st.session_state.wav_path, "rb") as fp:
            audio_bytes = fp.read()
            st.audio(audio_bytes, format="audio/wav")

        col_dl, col_proc = st.columns(2)
        processing_now = st.session_state.get("job_queued", False)

        # Download button
        with col_dl:
            st.download_button(
                "📥 Download Recording",
                audio_bytes,
                file_name="session.wav",
                mime="audio/wav",
            )

        # “Process recording” button
        with col_proc:
            if st.button(
                "⏳ Processing…" if processing_now else "⚙️ Process Recording",
                type="primary",
                disabled=processing_now,
            ):
                payload: Dict[str, Any] = dict(
                    user_id=st.session_state.user_id,
                    doctor_name=st.session_state.doctor_name,
                    patient_name=st.session_state.patient_name,
                    date_selected=st.session_state.date_selected,
                    audio_path=st.session_state.wav_path,
                )
                fut = enqueue_job(payload)
                st.session_state.update(
                    job_future=fut, job_queued=True, wizard_step=Step.PROCESSING
                )
                # register in sidebar job tracker
                add_job(
                    fut,
                    meta={
                        "patient": st.session_state.patient_name,
                        "doctor": st.session_state.doctor_name,
                        "date": str(st.session_state.date_selected),
                        "session_id": "",
                    },
                )
                st.rerun()
        return

    # ─────────────────────────────── 4️⃣  Background processing page
    if st.session_state.wizard_step == Step.PROCESSING:
        fut = st.session_state.get("job_future")
        if fut and fut.done():
            result = fut.result()
            if err := result.get("pipeline_error"):
                st.error(f"🚨 {err}")
                # reset so the user can try again
                st.session_state.update(
                    job_future=None, job_queued=False, wizard_step=Step.READY
                )
                return
            st.session_state.update(result, job_queued=False, wizard_step=Step.RESULTS)
            st.rerun()
        st.info("⏳ Processing in the background…")
        st.button("🔄 Refresh", on_click=st.rerun)
        return

    # ─────────────────────────────── 5️⃣  Results / editable summary
    if st.session_state.wizard_step == Step.RESULTS:
        st.subheader("📄 Full Transcript")
        st.write(st.session_state.transcript)

        st.markdown("### 📝 Edit Summary")
        st.info("The fields below are AI-generated. Feel free to adjust.")

        sections = _parse_structured_summary(st.session_state.summary_raw)
        updated: Dict[str, str] = {
            lbl: st.text_area(
                lbl + ":", value=sections.get(lbl, ""), key=f"summary_{lbl}", height=90
            )
            for lbl in SUMMARY_LABELS_EN
        }

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
            st.success("PDF ready – download below or attach to email.")
            st.rerun()

        if pdf_path := st.session_state.get("latest_pdf"):
            col_dl, col_mail = st.columns(2)

            # direct download
            with col_dl, open(pdf_path, "rb") as fp:
                st.download_button("📥 Download Summary", fp, file_name="summary.pdf")

            # optional e-mail
            with col_mail:
                default_email = st.session_state.get(
                    "user_email"
                ) or st.session_state.get("user_name", "")
                to_addr = st.text_input(
                    "✉️ Send to (email)", value=default_email, key="send_to_email"
                )
                if st.button("📧 Email PDF", disabled=not to_addr.strip()):
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
