# nlp/transcribe.py
from __future__ import annotations
from utils.openai_client import get_openai_client as _get_client


def _fast_stream(client, wav_path: str) -> str:
    """Streaming GPT-4o-mini transcription, plain text."""
    with open(wav_path, "rb") as f:
        chunks = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
            language="ar",
            stream=True,
            response_format="text",  # fastest path (no timestamps)
        )
        return "".join(chunk.text for chunk in chunks)


def transcribe_audio(audio_file_path: str) -> str:
    """
    ① try GPT-4o-mini-transcribe (streaming)
    ② fall back to Whisper-1 if needed
    ③ tag <doctor>/<patient> using GPT-4o-mini
    """
    client = _get_client()

    # ① fast path
    try:
        raw = _fast_stream(client, audio_file_path)
    except Exception:  # noqa: BLE001  (brittle-protect)
        # ② fallback
        with open(audio_file_path, "rb") as f:
            raw = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ar",
            ).text

    # ③ speaker tagging
    prompt = f"""
    Segment the following Arabic dialogue into lines, each prefixed by either
    <doctor> or <patient>. Do not add any other text.

    Transcript:
    {raw}
    """
    try:
        tagged = (
            client.chat.completions.create(
                model="gpt-4o-mini",
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
            .choices[0]
            .message.content.strip()
        )
        return tagged
    except Exception:
        return raw
