# utils/secret.py
from __future__ import annotations
import os
import streamlit as st


def get(key: str, *, default: str | None = None) -> str:
    """
    Fetch a secret value in a way that works both **locally** and on
    **Streamlit Cloud**.

    1. If the key exists in st.secrets  → return it.
    2. Else fall back to os.environ (what `python-dotenv` fills when
       you're running locally with a .env file).
    3. If the key is still missing and no default was given  → raise KeyError.

    Parameters
    ----------
    key : str
        The secret name, e.g. "OPENAI_API_KEY".
    default : str | None
        Optional value to return when the secret is missing.
    """
    # 1️⃣  Streamlit Cloud / st.secrets (also works locally if you set them)
    if key in st.secrets:
        return st.secrets[key]

    # 2️⃣  Local .env file or real environment vars
    val = os.getenv(key, default)

    # 3️⃣  Complain loudly if still missing
    if val is None:
        raise KeyError(f"Missing secret: {key}")

    return val
