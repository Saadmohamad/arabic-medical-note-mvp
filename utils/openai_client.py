# utils/openai_client.py
from __future__ import annotations
import openai
from utils.secret import get as _secret

# ------------------------------------------------------------
# One global OpenAI client, shared by all threads.
# ------------------------------------------------------------
_CLIENT: openai.OpenAI | None = None


def get_openai_client() -> openai.OpenAI:
    """
    Return a singleton OpenAI client.

    Using a plain module-level variable avoids Streamlit’s cache,
    so worker threads don’t complain about missing ScriptRunContext.
    """
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = openai.OpenAI(api_key=_secret("OPENAI_API_KEY"))
    return _CLIENT
