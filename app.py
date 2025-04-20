import streamlit as st
from db.models import setup_database, get_recent_sessions
from ui.session_ui import session_interaction
from ui.login_ui import login_flow

setup_database()

st.set_page_config(page_title="ANE Arabic Medical Note Taker", layout="centered")

if not login_flow():
    st.warning("⚠️ الرجاء تسجيل الدخول أولًا.")
    st.stop()

st.title("📋 مدوّن الملاحظات الطبية بالعربية للطوارئ (ANE)")


def reset_session_state_for_new_session():
    keys_to_clear = [
        "wizard_step",
        "doctor_name",
        "patient_name",
        "date_selected",
        "audio_bytes",
        "audio_file_path",
        "transcript",
        "summary_raw",
        "analysis_ready",
        "keywords",
        "diagnoses",
        "new_session",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


with st.sidebar:
    st.header("التحكم في الجلسة")
    if st.button("جلسة جديدة"):
        reset_session_state_for_new_session()
        st.session_state["new_session"] = True
        st.rerun()

    st.markdown("---")
    st.subheader("📂 الجلسات الأخيرة")
    sessions = get_recent_sessions(limit=5)
    for row in sessions:
        st.write(f"🗓️ {row[0].strftime('%Y-%m-%d')} | 👤 {row[1]}\n🔎 {row[2][:100]}...")

if st.session_state.get("new_session"):
    session_interaction()
