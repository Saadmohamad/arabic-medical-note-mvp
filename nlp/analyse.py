from __future__ import annotations
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# One shared client for all requests
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_SYMPTOM = "أنت مساعد طبي متخصص في معالجة اللغة. استخرج كلمات مفتاحية للأعراض فقط. لا تضف شرحاً."  # noqa: E501
SYSTEM_DIAGNOSIS = (
    "أنت مساعد طبي خبير في التشخيص. اقترح تشخيصات محتملة بناءً على النص."  # noqa: E501
)


# -----------------------------------------------------------------------------
# 🔑  Public functions
# -----------------------------------------------------------------------------


def extract_symptom_keywords(summary: str, transcript: str) -> str:
    """Return Arabic symptom keywords found in summary + transcript."""

    prompt = f"""
    استخرج الكلمات المفتاحية المتعلقة بالأعراض من النص التالي، مفصولة بفواصل:

    الملخص:
    {summary}

    النص الكامل:
    {transcript}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # cheaper + fast; change if needed
            messages=[
                {"role": "system", "content": SYSTEM_SYMPTOM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=128,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover – surfaced to UI
        raise RuntimeError(f"Symptom keyword extraction failed: {exc}") from exc


def extract_possible_diagnoses(summary: str, transcript: str) -> str:
    """Return possible diagnoses mentioned or implied in the text."""

    prompt = f"""
    استناداً إلى الملخص والنص الكامل، حدد أي تشخيصات محتملة تم ذكرها أو الإشارة إليها. قابلها في نقاط مختصرة:

    الملخص:
    {summary}

    النص الكامل:
    {transcript}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_DIAGNOSIS},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Diagnosis extraction failed: {exc}") from exc
