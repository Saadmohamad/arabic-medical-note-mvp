# nlp/summarise.py
from __future__ import annotations
import json
import logging
import textwrap
from typing import Dict

from utils.llm_helpers import safe_chat_completion

logger = logging.getLogger(__name__)

# Schema keys for structured output (English only)
SCHEMA_KEYS = [
    "Patient Complaint",
    "Clinical Notes",
    "Diagnosis",
    "Treatment Plan",
]

# Enhanced System prompt – explicitly English output instructions
SYSTEM = textwrap.dedent(
    """
    You are an experienced clinical scribe.
    Read the following Arabic medical dialogue and RETURN valid JSON with exactly these English keys:
      Patient Complaint
      Clinical Notes
      Diagnosis
      Treatment Plan

    All values MUST be in English only.
    Always include all keys, even if the value is an empty string.
    No other text or fields are allowed.
    """
).strip()


def _empty_note() -> Dict[str, str]:
    """Return an empty note dict with all required keys."""
    return {k: "" for k in SCHEMA_KEYS}


def summarize_transcript(
    transcript: str,
    *,
    tone: str = "telegraphic",
    primary_model: str = "gpt-4o-mini",
    fallback_model: str = "gpt-3.5-turbo",
    **kwargs,
) -> str:
    """
    Arabic transcript (doctor/patient lines) → English structured note (JSON).
    Returns *stringified JSON* guaranteed to have every schema key.
    Raises RuntimeError on repeated LLM failure – caller catches it.
    """

    # Defensive shorten if transcript is enormous
    if len(transcript) > 15_000:  # ≈10-12k tokens
        logger.warning(
            "Transcript too long (%d chars) – truncating tail", len(transcript)
        )
        transcript = transcript[:15_000]

    # Craft prompt
    style = (
        "Use short bullet points." if tone == "telegraphic" else "Write full sentences."
    )
    user_msg = f"""{style}

Conversation (Arabic) is between triple backticks:
```{transcript}```
"""

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]

    # Call LLM with automatic fallback / retries
    try:
        raw = safe_chat_completion(
            messages,
            primary_model=primary_model,
            fallback_model=fallback_model,
            max_tokens=700,  # breathing room
            response_format={"type": "json_object"},
            **kwargs,
        )
    except RuntimeError as e:
        logger.error("LLM summarisation failed: %s", e)
        raise

    # Post-process / validate
    note = _empty_note()
    try:
        note.update(json.loads(raw))
    except json.JSONDecodeError:
        logger.warning("Model returned non-JSON; raw response kept in Diagnosis field")
        note["Diagnosis"] = raw.strip()

    # Ensure all keys exist (model often misses one when empty)
    serialised = json.dumps(note, ensure_ascii=False)
    logger.debug("Final summary JSON: %s", serialised)
    return serialised
