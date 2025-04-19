import speech_recognition as sr
from nlp.transcribe import transcribe_audio
import tempfile

def recognize_doctor_name_from_voice(timeout: int = 5, phrase_limit: int = 5) -> str:
    """
    Captures Arabic voice input via microphone and returns transcribed name.

    Args:
        timeout (int): Seconds to wait for speech start.
        phrase_limit (int): Max seconds to capture speech.

    Returns:
        str: Transcribed doctor name in Arabic.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Say your name in Arabic...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio.get_wav_data())
                doctor_name = transcribe_audio(tmp.name)
                return doctor_name.strip()
        except Exception as e:
            raise RuntimeError(f"Voice recognition failed: {e}")
