import streamlit as st
from db.models import create_user, authenticate_user, get_user_id, user_exists


def clear_session():
    keys = list(st.session_state.keys())
    for key in keys:
        del st.session_state[key]


def login_flow():
    """
    Handles user login, signup, and logout.
    Returns True if the user is authenticated.
    """
    st.sidebar.header("🔐 Account")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = ""

    if st.session_state.logged_in:
        st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
        if st.sidebar.button("Log Out"):
            clear_session()
            st.rerun()
        return True

    mode = st.sidebar.radio("Select Action:", ("Login", "Sign Up", "Forgot Password"))
    email = st.sidebar.text_input("📧 Email")

    if mode in ["Login", "Sign Up"]:
        password = st.sidebar.text_input("🔑 Password", type="password")

    action_btn = st.sidebar.button("Continue")

    if action_btn:
        if mode == "Login":
            if authenticate_user(email, password):
                clear_session()
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_id = get_user_id(email)
                st.sidebar.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.sidebar.error("❌ Incorrect email or password.")

        elif mode == "Sign Up":
            if not email or not password:
                st.sidebar.error("❌ Please enter both email and password.")
            else:
                if user_exists(email):
                    st.sidebar.error("❌ Email already in use. Try logging in.")
                else:
                    create_user(email, password)
                    st.sidebar.success("✅ Account created! You can now log in.")

        elif mode == "Forgot Password":
            if email:
                # TODO: Implement your email reset logic here
                st.sidebar.info(
                    "📩 If the email is registered, reset instructions will be sent."
                )
            else:
                st.sidebar.error("❌ Please enter your email.")

    return st.session_state.logged_in
