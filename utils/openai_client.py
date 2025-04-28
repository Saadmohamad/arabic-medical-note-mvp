from __future__ import annotations
import streamlit as st
from utils.secret import get as _secret


@st.cache_resource(ttl=60 * 60, show_spinner="🔌 Connecting to OpenAI…")
def get_openai_client():
    """Singleton OpenAI client (cached per worker)."""
    import openai  # lazy-load heavy module

    return openai.OpenAI(api_key=_secret("OPENAI_API_KEY"))
