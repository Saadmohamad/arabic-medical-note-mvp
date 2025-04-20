from __future__ import annotations
import re


def normalize_arabic_for_nlp(text: str) -> str:
    """
    Normalize Arabic text for downstream NLP:
     - map all forms of alef (أ إ آ) → ا
     - map final-yeh (ى) → ي
     - strip tatweel and diacritics as before
    """
    # strip tatweel & diacritics
    text = text.replace("ـ", "")
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]", "", text)
    # normalize alef
    text = re.sub(r"[إأآا]", "ا", text)
    # normalize yeh
    text = text.replace("ى", "ي")
    # collapse whitespace
    return " ".join(text.split())
