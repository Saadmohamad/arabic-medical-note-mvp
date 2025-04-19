import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file_path):
    """
    Transcribes Arabic audio using OpenAI Whisper (new SDK format).

    Args:
        audio_file_path (str): Path to the audio file (.wav/.mp3).

    Returns:
        str: Transcribed Arabic text.
    """
    try:
        with open(audio_file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ar"
            )
        return transcript.text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
