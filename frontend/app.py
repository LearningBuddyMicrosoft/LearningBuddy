import streamlit as st
from pages.testpages.styles1 import apply_custom_css
# ── Session state defaults ────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "attempt_id" not in st.session_state:
    st.session_state.attempt_id = None
# ── Register all pages explicitly so Streamlit finds them in the subdirectory ─
# st.navigation() bypasses the automatic pages/ discovery and lets you point
# to any file path relative to this script.
pg = st.navigation(
    [
        st.Page("pages/testpages/login.py",         title="Login",         url_path="login"),
        st.Page("pages/testpages/dashboard.py",     title="Dashboard",     url_path="dashboard"),
        st.Page("pages/testpages/subject.py",       title="Switch Topic",  url_path="topic"),
        st.Page("pages/testpages/upload.py",        title="Upload Files",  url_path="upload"),
        st.Page("pages/testpages/generate_quiz.py", title="Generate Quiz", url_path="generate-quiz"),
        st.Page("pages/testpages/take_quiz.py",     title="Take Quiz",     url_path="take-quiz"),
        st.Page("pages/testpages/results.py",       title="View Results",  url_path="results"),
        st.Page("pages/testpages/progress.py",      title="View Progress", url_path="progress"),
    ],
    # position="hidden",  # hides the default sidebar nav; each page manages its own navigation
)
pg.run()
