# nlp/transcribe.py
from __future__ import annotations
import logging
import time
from tenacity import retry, wait_exponential, stop_after_attempt
from utils.openai_client import get_openai_client
from openai import RateLimitError

TRANSCRIPTION_MODEL = "whisper-1"
TAGGING_MODEL = "gpt-4o-mini"
LANGUAGE = "ar"

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────── Whisper
@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),  # ↑ 60 s
)
def _whisper(client, file):
    return client.audio.transcriptions.create(
        model=TRANSCRIPTION_MODEL,
        file=file,
        language=LANGUAGE,
    )


# ──────────────────────────────────────────────────────────── Tag speakers
@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),
)
def _tag_chunk(client, chunk: str) -> str:
    prompt = f"""Segment the following Arabic dialogue into lines, each prefixed by
either <doctor> or <patient>. Do not add any other text.

Transcript:
{chunk}
"""
    resp = client.chat.completions.create(
        model=TAGGING_MODEL,
        messages=[
            {
                "role": "system",
                "content": "أنت مساعد طبي يساعد في وسم كل جملة بعلامة المتكلم.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=1024,
    )
    return resp.choices[0].message.content.strip()


def _chunk(lines, n):
    for i in range(0, len(lines), n):
        yield lines[i : i + n]


# ───────────────────────────────────────────────────────────── Public API
def transcribe_audio(path: str) -> str:
    """
    1. Whisper transcription  → 2. Speaker tagging (chunk-safe).
    Returns *""* when Whisper fails so the caller can surface a pipeline error
    without crashing.
    """
    client = get_openai_client()

    # ① Whisper
    try:
        start = time.time()
        with open(path, "rb") as f:
            txt = _whisper(client, f).text
        logger.info("Whisper done in %.1fs (%d chars)", time.time() - start, len(txt))
    except (RateLimitError, Exception):
        logger.exception("Whisper failed", exc_info=True)
        return ""  # let caller flag pipeline_error

    # ② Speaker tagging (chunked to avoid context overflow)
    lines = txt.splitlines()
    tagged_blocks = []
    for chunk in _chunk(lines, 180):  # ≈180 lines ≈1500 tokens
        try:
            tagged_blocks.append(_tag_chunk(client, "\n".join(chunk)))
        except Exception as e:
            logger.warning("Tagging chunk failed (%s), keeping raw lines", e)
            tagged_blocks.append("\n".join(chunk))
    return "\n".join(tagged_blocks)
