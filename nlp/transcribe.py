from __future__ import annotations
import logging
import time
from tenacity import retry, wait_exponential, stop_after_attempt
from utils.openai_client import get_openai_client
from openai import RateLimitError

TRANSCRIPTION_MODEL = "gpt-4o-transcribe"
TAGGING_MODEL = "gpt-4o-mini"
LANGUAGE = "ar"

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────── Whisper
@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),  # ↑ 60 s
)
def _whisper(client, file, prompt=""):
    kwargs = dict(
        model=TRANSCRIPTION_MODEL,
        file=file,
        language=LANGUAGE,
        temperature=0,
        prompt=prompt,
    )

    # gpt-4o-transcribe & gpt-4o-mini-transcribe only do "json"/"text"
    if TRANSCRIPTION_MODEL.startswith("gpt-4o"):
        kwargs["response_format"] = "json"  # segments not available
    else:
        kwargs["response_format"] = "verbose_json"
        kwargs["timestamp_granularities"] = ["segment"]

    return client.audio.transcriptions.create(**kwargs)


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
def transcribe_audio(path: str, tagging: bool = False) -> str:
    """
    ① Whisper / gpt-4o transcription  → ② optional speaker tagging.
    Returns "" on Whisper failure so the caller can surface a pipeline error.
    """
    client = get_openai_client()
    rolling_prompt = ""

    try:
        start = time.time()
        with open(path, "rb") as f:
            resp = _whisper(client, f, prompt=rolling_prompt)

        # ─── normalise the response to plain text ────────────────────────────
        if hasattr(resp, "segments"):  # whisper-1 (verbose_json)
            txt = "\n".join(seg["text"] for seg in resp.segments)
        else:  # gpt-4o-transcribe (json/text)
            txt = resp.text

        logger.info(
            "Transcribe done in %.1fs (%d chars)", time.time() - start, len(txt)
        )

        # keep the last ~2 000 chars as rolling prompt for any *next* chunk
        rolling_prompt = (rolling_prompt + txt)[-2000:]

    except RateLimitError:
        logger.warning("Transcription rate-limited", exc_info=True)
        return ""
    except Exception:
        logger.exception("Transcription failed", exc_info=True)
        raise  # let real bugs surface instead of silent "" return

    # ─── optional speaker tagging ───────────────────────────────────────────
    if not tagging:
        return txt

    tagged_blocks = []
    for chunk in _chunk(txt.splitlines(), 100):  # ≤100 lines ≈ 800 tokens
        try:
            tagged_blocks.append(_tag_chunk(client, "\n".join(chunk)))
        except Exception as e:
            logger.warning("Tagging chunk failed (%s); keeping raw lines", e)
            tagged_blocks.append("\n".join(chunk))

    return "\n".join(tagged_blocks)
