import os
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization", use_auth_token=os.getenv("HUGGINGFACE_TOKEN")
)


def diarize_audio(audio_path: str) -> str:
    """
    Perform speaker diarization on the audio and return a text summary of speaker segments.

    Args:
        audio_path (str): Path to .wav audio file.

    Returns:
        str: Speaker segments description.
    """
    diarization = pipeline(audio_path)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(f"{speaker} [{turn.start:.1f}s - {turn.end:.1f}s]")
    return "\n".join(segments)
