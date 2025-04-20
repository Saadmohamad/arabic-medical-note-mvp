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
    st.sidebar.header("🔐 الحساب")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = ""

    if st.session_state.logged_in:
        st.sidebar.success(f"مسجل دخول: {st.session_state.user_email}")
        if st.sidebar.button("تسجيل الخروج"):
            clear_session()
            st.rerun()
        return True

    mode = st.sidebar.radio(
        "اختر الإجراء:", ("تسجيل الدخول", "إنشاء حساب", "نسيت كلمة المرور")
    )

    email = st.sidebar.text_input("📧 البريد الإلكتروني")

    if mode in ["تسجيل الدخول", "إنشاء حساب"]:
        password = st.sidebar.text_input("🔑 كلمة المرور", type="password")

    action_btn = st.sidebar.button("متابعة")

    if action_btn:
        if mode == "تسجيل الدخول":
            if authenticate_user(email, password):
                clear_session()
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_id = get_user_id(email)
                st.sidebar.success("✅ تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.sidebar.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة.")

        elif mode == "إنشاء حساب":
            if not email or not password:
                st.sidebar.error("❌ يرجى إدخال البريد الإلكتروني وكلمة المرور.")
            else:
                if user_exists(email):
                    st.sidebar.error(
                        "❌ البريد الإلكتروني مستخدم بالفعل. حاول تسجيل الدخول."
                    )
                else:
                    create_user(email, password)
                    st.sidebar.success("✅ تم إنشاء الحساب! يمكنك الآن تسجيل الدخول.")
        elif mode == "نسيت كلمة المرور":
            if email:
                # TODO: Implement your email reset logic here
                st.sidebar.info(
                    "📩 إذا كان البريد الإلكتروني مسجلاً ستصلك التعليمات قريباً."
                )
            else:
                st.sidebar.error("❌ أدخل بريدك الإلكتروني.")

    return st.session_state.logged_in
