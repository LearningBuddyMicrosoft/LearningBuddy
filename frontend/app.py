import streamlit as st

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
        st.Page("pages/testpages/manage.py",        title="Manage",        url_path="manage"),
        st.Page("pages/testpages/generate_quiz.py", title="Generate Quiz", url_path="generate-quiz"),
        st.Page("pages/testpages/take_quiz.py",     title="Take Quiz",     url_path="take-quiz"),
        st.Page("pages/testpages/results.py",       title="Results",       url_path="results"),

        st.Page("pages/testpages/attempts.py",       title="Past Attempts",   url_path="attempts"),
        st.Page("pages/testpages/attempt_review.py", title="Review Attempt",  url_path="attempt-review"),
    ],
    position="sidebar",  # hides the default sidebar nav; each page manages its own navigation
)
pg.run()
