import os
import streamlit as st
from db.models import setup_database, get_recent_sessions
from ui.session_ui import session_interaction


required_vars = ["OPENAI_API_KEY", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
for var in required_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")


st.set_page_config(page_title="ANE Arabic Medical Note Taker", layout="centered")
st.title("📋 ANE Arabic Medical Note Taker")

# Initial DB setup
setup_database()

# Sidebar navigation
with st.sidebar:
    st.header("Session Control")
    if st.button("Start New Session"):
        st.session_state["new_session"] = True

    st.markdown("---")
    st.subheader("📂 Session History")
    sessions = get_recent_sessions(limit=5)
    for row in sessions:
        st.write(f"🗓️ {row[0].strftime('%Y-%m-%d')} | 👤 {row[1]}\n🔎 {row[2][:100]}...")

# Main view logic
if "new_session" in st.session_state and st.session_state.new_session:

    # Load session interaction UI
    session_interaction()
