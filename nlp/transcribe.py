from utils.openai_client import get_openai_client as _get_openai_client


def transcribe_audio(audio_file_path):
    """
    Transcribes Arabic audio using OpenAI Whisper (new SDK format).

    Args:
        audio_file_path (str): Path to the audio file (.wav/.mp3).

    Returns:
        str: Transcribed Arabic text.
    """
    try:
        client = _get_openai_client()
        with open(audio_file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=f, language="ar"
            )
        raw = transcript.text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
    # GPT‑based speaker‑tagging
    tagging_prompt = f"""
    Segment the following Arabic dialogue into lines, each prefixed by either <doctor> or <patient> based on who is speaking. Do not add any other text.

    Transcript:
    {raw}
    """
    try:
        tag_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد طبي يساعد في وسم كل جملة بعلامة المتكلم.",
                },
                {"role": "user", "content": tagging_prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )
        return tag_resp.choices[0].message.content.strip()
    except Exception:
        # if tagging fails, fall back to the raw transcript
        return raw
