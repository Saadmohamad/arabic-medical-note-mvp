import streamlit as st
from db.models import setup_database, get_session_details_by_index
from ui.session_ui import (
    session_interaction,
    _parse_structured_summary,
    _combine_structured_summary,
    SUMMARY_LABELS_AR,
)
from ui.login_ui import login_flow
from utils.helpers import export_summary_pdf

setup_database()
st.set_page_config(page_title="ANE Arabic Medical Note Taker", layout="centered")

if not login_flow():
    st.warning("⚠️ الرجاء تسجيل الدخول أولًا.")
    st.stop()

st.title("📋 مدوّن الملاحظات الطبية بالعربية للطوارئ (ANE)")

# Navigation
view_choice = st.sidebar.radio("انتقل إلى:", ("جلسة جديدة", "📂 الجلسات السابقة"))

# ----------------- Page: New Session ------------------
if view_choice == "جلسة جديدة":

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

    if st.sidebar.button("🔁 بدء جلسة جديدة"):
        reset_session_state_for_new_session()
        st.session_state["new_session"] = True
        st.rerun()

    if st.session_state.get("new_session"):
        session_interaction()

# ----------------- Page: Past Sessions ------------------
elif view_choice == "📂 الجلسات السابقة":
    st.header("📂 الجلسات السابقة")

    all_sessions = get_session_details_by_index(st.session_state.user_id)
    if not all_sessions:
        st.info("لا توجد جلسات محفوظة.")
        st.stop()

    session_labels = [
        f"{row[1].strftime('%Y-%m-%d')} – 👨‍⚕️ {row[2]} | 👤 {row[3]}"
        for row in all_sessions
    ]
    selected_idx = st.selectbox(
        "اختر جلسة سابقة:",
        range(len(session_labels)),
        format_func=lambda i: session_labels[i],
    )

    session_id, date_sel, doctor_name, patient_name, transcript, summary = all_sessions[
        selected_idx
    ]

    st.subheader("📄 النص الكامل")
    st.write(transcript)

    st.subheader("📝 ملخص الجلسة")
    sections = _parse_structured_summary(summary)
    updated: dict[str, str] = {}
    for lbl in SUMMARY_LABELS_AR:
        key = f"past_summary_{lbl}"
        updated[lbl] = st.text_area(
            lbl + ":", value=sections.get(lbl, ""), key=key, height=90
        )

    if st.button("📄 تنزيل PDF", key="past_pdf_btn"):
        combined = _combine_structured_summary(updated)
        pdf_path = export_summary_pdf(
            doctor_name, patient_name, date_sel, combined, transcript
        )
        with open(pdf_path, "rb") as fp:
            st.download_button(
                "📥 تنزيل الملخص", fp, file_name="summary.pdf", key="download_btn"
            )
