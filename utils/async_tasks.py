# utils/async_tasks.py
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Dict

from db.models import (
    get_existing_session_by_hash,
    insert_doctor,
    insert_patient,
    insert_session,
)
from nlp.transcribe import transcribe_audio
from nlp.summarise import summarize_transcript
from utils.audio_io import file_sha256

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Thread pool for background execution
# ─────────────────────────────────────────────────────────────────────────────
_EXECUTOR: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=2)


def _heavy_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    audio_path = payload["audio_path"]
    audio_hash = file_sha256(audio_path)

    # ① Cache hit?
    if existing := get_existing_session_by_hash(payload["user_id"], audio_hash):
        payload.update(existing, analysis_ready=True)
        return payload

    # ② Transcription
    transcript = transcribe_audio(audio_path)
    if not transcript:
        payload["pipeline_error"] = "Transcription failed"
        return payload

    # ③ Summarisation
    try:
        summary = summarize_transcript(transcript)
        summary_dict = json.loads(summary)
    except RuntimeError as e:
        payload["pipeline_error"] = str(e)
        return payload

    # ④ Persistence
    doc_id = insert_doctor(payload["doctor_name"])
    pat_id = insert_patient(payload["patient_name"])
    sess_id = insert_session(
        payload["user_id"],
        doc_id,
        pat_id,
        payload["date_selected"],
        transcript,
        summary_dict.get("Patient Complaint", ""),
        summary_dict.get("Clinical Notes", ""),
        summary_dict.get("Diagnosis", ""),
        summary_dict.get("Treatment Plan", ""),
        audio_path,
        audio_hash,
    )

    payload.update(
        session_id=sess_id,
        transcript=transcript,
        summary_raw=summary,
        analysis_ready=True,
    )
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# Public API: enqueue the above on a worker thread
# ─────────────────────────────────────────────────────────────────────────────
def enqueue_job(payload: Dict[str, Any]) -> Future[Dict[str, Any]]:
    """
    Schedule `_heavy_pipeline` to run in the background.

    Returns a Future whose result() is the enriched payload.
    """
    return _EXECUTOR.submit(_heavy_pipeline, payload)
