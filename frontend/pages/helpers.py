import copy
from datetime import datetime
import streamlit as st
# ...existing code...

def initialize_session_state():
    if "users" not in st.session_state:
        st.session_state.users = {}
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "Landing"
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "theme" not in st.session_state:
        st.session_state.theme = "Dark"
    if "q_index" not in st.session_state:
        st.session_state.q_index = 0
    if "selected_answers" not in st.session_state:
        st.session_state.selected_answers = {}
        if"selected_topic" not in st.session_state:
            st.session_state.selected_topic = ""
    if "flagged_questions" not in st.session_state:
        st.session_state.flagged_questions = set()
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "percentage" not in st.session_state:
        st.session_state.percentage = 0
    if "quiz_history" not in st.session_state:
        st.session_state.quiz_history = []
    if "history_review_index" not in st.session_state:
        st.session_state.history_review_index = None
    if "review_mode" not in st.session_state:
        st.session_state.review_mode = "All"
    # ...existing code...

def reset_quiz():
    st.session_state.q_index = 0
    st.session_state.selected_answers = {}
    st.session_state.flagged_questions = set()
    st.session_state.score = 0
    st.session_state.percentage = 0
    st.session_state.review_mode = "All"
    st.session_state.history_review_index = None

def submit_quiz(questions):
    score = sum(
        1
        for i, q in enumerate(questions)
        if st.session_state.selected_answers.get(i, "").strip() == q["answer"].strip()
    )
    percentage = round((score / len(questions)) * 100) if questions else 0

    st.session_state.score = score
    st.session_state.percentage = percentage

    topic = st.session_state.get("selected_topic'") or "None"
    st.session_state.quiz_history.append({
        "questions": copy.deepcopy(questions),
        "selected_answers": dict(st.session_state.selected_answers),
        "score": score,
        "total": len(questions),
        "percentage": percentage,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "flagged_count": len(st.session_state.flagged_questions),
        "topic": st.session_state.get("selected_topic") or "General"
    })

    st.session_state.history_review_index = len(st.session_state.quiz_history) - 1
    st.session_state.page = "Review"