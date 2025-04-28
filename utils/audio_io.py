import tempfile


def bytes_to_wav(raw: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(raw)
    tmp.close()
    return tmp.name
