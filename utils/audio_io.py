# utils/audio_io.py
import tempfile
import hashlib
import pathlib


def file_sha256(path: str | pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def bytes_to_wav(raw: bytes) -> str:
    """Convert raw PCM bytes to a temporary WAV file and return its path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(raw)
    tmp.close()
    return tmp.name
