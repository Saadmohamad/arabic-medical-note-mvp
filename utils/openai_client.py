# nlp/openai_client.py
from __future__ import annotations
import streamlit as st
import openai
from utils.secret import get as get_secret  # ← the helper we wrote earlier

#   (or use st.secrets[...] directly)


@st.cache_resource(ttl=60 * 60, show_spinner="🔌 Connecting to OpenAI…")
def get_openai_client() -> openai.OpenAI:
    """
    Return a singleton OpenAI client that is cached per Streamlit worker.
    A new client is created only if:
      • the container is restarted, or
      • 60 min (ttl) have passed.
    """
    api_key = get_secret("OPENAI_API_KEY")
    return openai.OpenAI(api_key=api_key)
