import streamlit as st
from db.models import authenticate_user, get_user_id


def clear_session():
    keys = list(st.session_state.keys())
    for key in keys:
        del st.session_state[key]


def login_flow() -> bool:
    """Simple *username + password* login. Returns **True** when authenticated."""
    st.sidebar.header("🔐 Login")

    # Ensure deterministic keys exist so Streamlit widgets don’t complain
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_name = ""

    # ----- Already logged‑in branch -----
    if st.session_state.logged_in:
        st.sidebar.success(f"Logged in as: {st.session_state.user_name}")
        if st.sidebar.button("Log Out"):
            clear_session()
            st.rerun()
        return True

    # ----- Credential entry -----
    user_name = st.sidebar.text_input("👤 Username")
    password = st.sidebar.text_input("🔑 Password", type="password")

    if st.sidebar.button("Log In"):
        if authenticate_user(user_name, password):
            # Freshen the session before writing new state
            clear_session()
            st.session_state.logged_in = True
            st.session_state.user_name = user_name
            st.session_state.user_id = get_user_id(user_name)
            st.sidebar.success("✅ Logged in successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Incorrect username or password.")

    return st.session_state.logged_in
