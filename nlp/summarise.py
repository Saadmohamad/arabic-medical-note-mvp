from typing import Literal
from utils.openai_client import get_openai_client


client = get_openai_client()


def summarize_transcript(
    transcript: str,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 512,
    tone: Literal["telegraphic", "full"] = "telegraphic",
) -> str:
    """
    Convert an **Arabic** doctor-patient conversation into an English clinical note.

    Parameters
    ----------
    transcript : str
        Arabic transcript, already tagged <doctor>/<patient>.
    model : str
        Chat‐completion model to use.
    temperature : float
        A touch of temperature helps the model re-phrase naturally without hallucinating.
    max_tokens : int
        Hard cap on summary length.
    tone : {'telegraphic', 'full'}
        'telegraphic' gives short bullet points; 'full' gives prose sentences.
    """
    style_hint = (
        "Use terse, bullet-point phrases."
        if tone == "telegraphic"
        else "Write complete sentences that flow naturally."
    )

    user_prompt = f"""You are a medical assistant.
The following conversation is in Arabic—read it carefully but **write your answer in English**.

Summarize the dialogue into structured clinical notes using *exactly* this template:
- Patient Complaint:
- Clinical Notes:
- Diagnosis (if any):
- Treatment Plan:

{style_hint}

Conversation (Arabic):
{transcript}
"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an experienced clinical scribe. "
                        "Stay faithful to the source; do not invent facts."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Summarization failed: {e}")
