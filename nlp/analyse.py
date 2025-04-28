from __future__ import annotations
from utils.openai_client import get_openai_client

client = get_openai_client()

# --------------------------------------------------------------------------- #
#  📜  System instructions (English answers only)                             #
# --------------------------------------------------------------------------- #

SYSTEM_SYMPTOM_EN = (
    "You are a clinical language assistant. "
    "Extract **only** symptom keywords from the user text, "
    "translate them to English, and return them as a comma-separated list. "
    "Do not add any commentary, diagnosis, or Arabic words."
)

SYSTEM_DIAGNOSIS_EN = (
    "You are an expert medical assistant. "
    "Suggest plausible differential diagnoses **in English** based solely on "
    "the user text. List each diagnosis on its own line with no extra prose. "
    "Do not give definitive conclusions and do not include Arabic words."
)

# --------------------------------------------------------------------------- #
#  🔑  Public helpers                                                         #
# --------------------------------------------------------------------------- #


def extract_symptom_keywords(
    summary: str,
    transcript: str,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 128,
) -> str:
    """
    Return English symptom keywords found in an Arabic summary + transcript.

    The caller passes Arabic text; the function normalises it for NLP, then
    asks GPT to surface only the symptom terms and translate them.
    """
    summary_norm = summary
    transcript_norm = transcript

    user_prompt = (
        "The following text is in Arabic. Read it carefully and reply ONLY "
        "with symptom keywords translated into English, comma-separated.\n\n"
        f"Arabic summary:\n{summary_norm}\n\nArabic transcript:\n{transcript_norm}"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_SYMPTOM_EN},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        raise RuntimeError(f"Symptom keyword extraction failed: {exc}") from exc


def extract_possible_diagnoses(
    summary: str,
    transcript: str,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 160,
) -> str:
    """
    Return a line-by-line English list of *possible* diagnoses mentioned
    or implied in the Arabic summary + transcript.

    Results are suggestions, not definitive conclusions.
    """
    summary_norm = summary
    transcript_norm = transcript

    user_prompt = (
        "The following content is in Arabic. Read it carefully and reply in "
        "English only. List any possible diagnoses that were mentioned or "
        "hinted at, one per line, without additional commentary.\n\n"
        f"Arabic summary:\n{summary_norm}\n\nArabic transcript:\n{transcript_norm}"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_DIAGNOSIS_EN},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        raise RuntimeError(f"Diagnosis extraction failed: {exc}") from exc
