from __future__ import annotations

import re
import tempfile
from pathlib import Path

import streamlit as st
from st_audiorec import st_audiorec

from nlp.transcribe import transcribe_audio

__all__ = ["recognize_doctor_name_from_voice"]


def _normalize_arabic(text: str) -> str:
    """Basic Arabic text normalisation: remove tatweel, diacritics, collapse ws."""
    # 1. Strip Kashida (tatweel)
    text = text.replace("ـ", "")
    # 2. Remove Arabic diacritics
    diacritics = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
    text = diacritics.sub("", text)
    # 3. Trim & collapse extra whitespace
    return " ".join(text.split())


def recognize_doctor_name_from_voice(ui_prompt: str | None = None) -> str:
    """Capture a 2‑4 second voice snippet and return the transcribed doctor name.

    Designed to run inside a Streamlit script. If the user hasn’t recorded yet
    the function returns an empty string so the caller can gracefully wait.
    """
    if ui_prompt:
        st.markdown(ui_prompt)

    audio_bytes: bytes | None = st_audiorec()

    if audio_bytes is None:
        # No recording yet – widget is either idle or still capturing
        return ""

    # Persist to a temporary WAV so Whisper can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path: Path = Path(tmp.name)

    # Transcribe via OpenAI Whisper
    raw_name: str = transcribe_audio(str(tmp_path))
    clean_name: str = _normalize_arabic(raw_name)

    return clean_name
