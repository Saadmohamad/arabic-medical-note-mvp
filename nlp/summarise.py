import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Create a client instance (new SDK format)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_transcript(transcript: str) -> str:
    """
    Summarizes an Arabic transcript of a doctor-patient conversation
    into a structured clinical note.
    """
    prompt = f"""
    أنت مساعد طبي. لخّص محادثة الطبيب مع المريض في ملاحظات طبية باستخدام البنية التالية:
    - شكوى المريض:
    - ملاحظات سريرية:
    - التشخيص (إذا وُجد):
    - خطة العلاج:

    المحادثة:
    {transcript}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "أنت مساعد طبي متمرس."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Summarization failed: {e}")
