import streamlit as st
from api_client import login, register

st.set_page_config(page_title="Login – Learning Buddy", page_icon="🎓", layout="centered")

if st.session_state.get("token"):
    st.switch_page("pages/testpages/dashboard.py")

st.markdown("""
<style>
.login-shell {
    max-width: 560px;
    margin: 4vh auto 0 auto;
}
.login-hero {
    padding: 1.4rem 1.5rem;
    border-radius: 22px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 14px 32px rgba(0,0,0,0.18);
    margin-bottom: 1rem;
}
.login-hero h1 {
    margin: 0;
    font-size: 2rem;
    line-height: 1.1;
}
.login-hero p {
    margin: 0.55rem 0 0 0;
    color: #cbd5e1;
    font-size: 1rem;
}
.login-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 1rem 1rem 0.8rem 1rem;
    border: 1px solid rgba(15,23,42,0.08);
    box-shadow: 0 10px 24px rgba(15,23,42,0.08);
}
.helper-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.8rem;
}
.helper-pill {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    background: #eef2ff;
    color: #334155;
    font-size: 0.85rem;
    font-weight: 600;
    border: 1px solid rgba(51,65,85,0.08);
}
div.stButton > button,
div[data-testid="stFormSubmitButton"] > button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="login-shell">', unsafe_allow_html=True)

st.markdown("""
<div class="login-hero">
    <h1>🎓 Learning Buddy</h1>
    <p>Your adaptive AI study assistant for building subjects, uploading materials, and generating smart quizzes.</p>
    <div class="helper-row">
        <span class="helper-pill">AI-powered quizzes</span>
        <span class="helper-pill">Topic-based learning</span>
        <span class="helper-pill">Instant feedback</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="login-card">', unsafe_allow_html=True)

tab_login, tab_register = st.tabs(["Log In", "Register"])

with tab_login:
    st.markdown("### Welcome back")
    st.caption("Log in to continue your study session.")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        if not username or not password:
            st.warning("Please enter both username and password.")
        else:
            with st.spinner("Signing you in..."):
                ok, err = login(username, password)

            if ok:
                st.success("Logged in successfully.")
                st.switch_page("pages/testpages/dashboard.py")
            else:
                st.error(err)

with tab_register:
    st.markdown("### Create your account")
    st.caption("Start building your personal study space.")

    with st.form("register_form"):
        new_username = st.text_input("Choose a username", placeholder="Pick a username")
        new_password = st.text_input("Choose a password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm password", type="password", placeholder="Re-enter your password")
        submitted_reg = st.form_submit_button("Create Account", use_container_width=True)

    if submitted_reg:
        if not new_username or not new_password or not confirm_password:
            st.warning("Please fill in all fields.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 6:
            st.warning("Use a password with at least 6 characters.")
        else:
            with st.spinner("Creating your account..."):
                ok, err = register(new_username, new_password)

            if ok:
                st.success("Account created successfully. You can now log in.")
            else:
                st.error(err)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)