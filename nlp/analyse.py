import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_symptom_keywords(summary: str, transcript: str) -> str:
    """
    Extracts symptom-related keywords from summary and transcript.

    Args:
        summary (str): Arabic medical summary.
        transcript (str): Arabic conversation transcript.

    Returns:
        str: Arabic list of keywords.
    """
    prompt = f"""
    استخرج الكلمات المفتاحية المتعلقة بالأعراض من النص التالي:

    الملخص:
    {summary}

    النص الكامل:
    {transcript}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد طبي متخصص في معالجة اللغة."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Symptom keyword extraction failed: {e}")

def extract_possible_diagnoses(summary: str, transcript: str) -> str:
    """
    Identifies potential diagnoses from the Arabic summary and transcript.

    Args:
        summary (str): Arabic medical summary.
        transcript (str): Arabic transcript of session.

    Returns:
        str: Diagnoses or suggestions (Arabic).
    """
    prompt = f"""
    استناداً إلى الملخص والنص الكامل، حدد أي تشخيصات محتملة تم ذكرها أو الإشارة إليها:

    الملخص:
    {summary}

    النص الكامل:
    {transcript}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد طبي خبير في التشخيص."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Diagnosis extraction failed: {e}")
