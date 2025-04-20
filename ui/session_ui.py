from __future__ import annotations


import datetime
import tempfile
import re
import streamlit as st

try:
    from st_audiorec import st_audiorec  # type: ignore
except ModuleNotFoundError:
    st.error(
        "❗ `streamlit-audiorec` not installed. Run `pip install streamlit-audiorec`. "
    )
    st.stop()

from nlp.transcribe import transcribe_audio
from nlp.summarise import summarize_transcript
from nlp.analyse import extract_symptom_keywords, extract_possible_diagnoses
from db.models import insert_doctor, insert_patient, insert_session, get_patient_names
from utils.helpers import export_summary_pdf

__all__ = ["session_interaction"]

SUMMARY_LABELS_AR = [
    "شكوى المريض",
    "ملاحظات سريرية",
    "التشخيص (إذا وُجد)",
    "خطة العلاج",
]


# -----------------------------------------------------------------------------
# 🖌️  Helpers
# -----------------------------------------------------------------------------


def _inject_rtl_css() -> None:
    st.markdown(
        """<style>body,.stApp{direction:rtl;text-align:right}</style>""",
        unsafe_allow_html=True,
    )


def _clean_line(line: str) -> str:
    return re.sub(r"^[\s\-•]+", "", line).strip()


def _parse_structured_summary(text: str) -> dict[str, str]:
    sections: dict[str, str] = {lbl: "" for lbl in SUMMARY_LABELS_AR}
    current: str | None = None
    for raw in text.splitlines():
        line = _clean_line(raw)
        for lbl in SUMMARY_LABELS_AR:
            if line.startswith(lbl):
                current = lbl
                parts = line.split(":", 1)
                sections[current] = parts[1].strip() if len(parts) > 1 else ""
                break
        else:
            if current:
                sections[current] += " " + line
    return sections


def _combine_structured_summary(sections: dict[str, str]) -> str:
    return "\n".join(f"- {lbl}: {val.strip()}" for lbl, val in sections.items())


# -----------------------------------------------------------------------------
# 🩺  UI Flow
# -----------------------------------------------------------------------------


def session_interaction() -> None:
    _inject_rtl_css()

    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1

    # ------------------------------ STEP 1 ----------------------------------
    if st.session_state.wizard_step == 1:
        st.subheader("🩺 تحديد الطبيب والمريض")
        doctor_name = st.text_input("👨‍⚕️ اسم الطبيب (بالعربية)")
        patient_sel = st.selectbox(
            "🧑‍🤝‍🧑 اختر المريض", options=[""] + get_patient_names()
        )
        if not patient_sel:
            patient_sel = st.text_input("أو أدخل اسم مريض جديد (بالعربية)")
        date_sel = st.date_input("📅 التاريخ", value=datetime.date.today())
        if st.button("التالي ➡️", disabled=not doctor_name):
            st.session_state.update(
                {
                    "doctor_name": doctor_name,
                    "patient_name": patient_sel,
                    "date_selected": date_sel,
                    "wizard_step": 2,
                }
            )
            st.rerun()
        return

    # ------------------------------ STEP 2 ----------------------------------
    if st.session_state.wizard_step == 2:
        st.subheader("🎙️ تسجيل الجلسة الصوتية")
        status = st.empty()
        bytes_rec = st_audiorec()
        if bytes_rec is None:
            status.markdown(
                "<span style='color:red;font-size:24px;animation:blinker 1s infinite'>●</span> جارٍ التسجيل…",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<style>@keyframes blinker{50%{opacity:0}}</style>",
                unsafe_allow_html=True,
            )
        else:
            status.success("تم تسجيل المقطع ✔️")
        if bytes_rec and st.session_state.get("audio_bytes") != bytes_rec:
            st.session_state.audio_bytes = bytes_rec
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(bytes_rec)
                st.session_state.audio_file_path = tmp.name
        st.button(
            "التالي ➡️",
            disabled="audio_file_path" not in st.session_state,
            on_click=lambda: st.session_state.update({"wizard_step": 3}),
        )
        return

    # ------------------------------ STEP 3 ----------------------------------
    if st.session_state.wizard_step == 3:
        st.subheader("📤 معالجة الصوت")
        audio_path: str = st.session_state.audio_file_path  # type: ignore

        # --------- Transcription (once) ---------
        if "transcript" not in st.session_state:
            with st.status("تفريغ الصوت…", expanded=False):
                st.session_state.transcript = transcribe_audio(audio_path)

        # --------- GPT Summary (once) ----------
        if "summary_raw" not in st.session_state:
            with st.status("تلخيص …", expanded=False):
                st.session_state.summary_raw = summarize_transcript(
                    st.session_state.transcript
                )

        # --------- Auto‑analysis (once) --------
        if not st.session_state.get("analysis_ready"):
            with st.spinner("تحليل الجلسة تلقائياً…"):
                st.session_state.keywords = extract_symptom_keywords(
                    st.session_state.summary_raw, st.session_state.transcript
                )
                st.session_state.diagnoses = extract_possible_diagnoses(
                    st.session_state.summary_raw, st.session_state.transcript
                )
                st.session_state.analysis_ready = True

            # Persist transcription & summary only once
            doc_id = insert_doctor(st.session_state.doctor_name)
            pat_id = insert_patient(st.session_state.patient_name)
            insert_session(
                doc_id,
                pat_id,
                st.session_state.date_selected,
                st.session_state.transcript,
                st.session_state.summary_raw,
                audio_path,
            )
            st.success("✅ تم حفظ الجلسة!")

        # ---------------- Transcript ----------------
        st.markdown("### 📄 النص الكامل")
        st.write(st.session_state.transcript)

        # ---------------- Editable summary ----------------
        st.markdown("### 📝 حرر الملخص")
        st.info(
            "تم ملء الحقول تلقائياً باستخدام تحليل الذكاء الاصطناعي. يمكنك تعديلها يدويًا."
        )

        sections = _parse_structured_summary(st.session_state.summary_raw)
        sections["ملاحظات سريرية"] = (
            sections.get("ملاحظات سريرية", "")
            + "\nالأعراض: "
            + st.session_state.keywords
        ).strip()
        sections["التشخيص (إذا وُجد)"] = st.session_state.diagnoses

        updated: dict[str, str] = {}
        for lbl in SUMMARY_LABELS_AR:
            key = f"summary_{lbl}"
            updated[lbl] = st.text_area(
                lbl + ":", value=sections.get(lbl, ""), key=key, height=90
            )

        # --------------- Export PDF -----------------------
        if st.button("📄 تصدير PDF"):
            combined = _combine_structured_summary(updated)
            pdf_path = export_summary_pdf(
                st.session_state.doctor_name,
                st.session_state.patient_name,
                st.session_state.date_selected,
                combined,
                st.session_state.transcript,
            )
            with open(pdf_path, "rb") as fp:
                st.download_button("📥 تنزيل الملخص", fp, file_name="summary.pdf")
        return
