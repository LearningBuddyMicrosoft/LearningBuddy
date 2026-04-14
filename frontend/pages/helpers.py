from copy import deepcopy
from datetime import datetime
import streamlit as st


def initialize_session_state():
    defaults = {
        "authenticated": False,
        "page": "AuthLanding",
        "auth_page": "Landing",
        "username": "",
        "users": {},
        "auth_mode": "Login",
        "theme": "Dark",
        "q_index": 0,
        "score": 0,
        "selected_answers": {},
        "flagged_questions": set(),
        "quiz_submitted": False,
        "quiz_history": [],
        "review_mode": "All",
        "questions": None,
        "history_review": None,
        "current_quiz_title": "Practice Quiz",
        "current_subject": "Uncategorized",
        "current_topic": "General",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_quiz():
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.selected_answers = {}
    st.session_state.flagged_questions = set()
    st.session_state.quiz_submitted = False
    st.session_state.review_mode = "All"
    st.session_state.history_review = None


def calculate_score(questions):
    score = 0
    for i, q in enumerate(questions):
        if st.session_state.selected_answers.get(i) == q["answer"]:
            score += 1
    return score


def submit_quiz(questions):
    wrong_questions = []
    for i, q in enumerate(questions):
        user_answer = st.session_state.selected_answers.get(i)
        if user_answer != q["answer"]:
         wrong_questions.append(q["q"])
    score = calculate_score(questions)
    st.session_state.score = score
    st.session_state.quiz_submitted = True

    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")

    history_entry = {
        "username": st.session_state.username,
        "quiz_title": st.session_state.get("current_quiz_title", "Practice Quiz"),
        "subject": st.session_state.get("current_subject", "Uncategorized"),
        "topic": st.session_state.get("current_topic", "General"),
        "score": score,
        "total": len(questions),
        "percentage": round((score / len(questions)) * 100),
        "timestamp": timestamp,
        "flagged_count": len(st.session_state.flagged_questions),
        "wrong_questions": wrong_questions,
        "questions": deepcopy(questions),
        "selected_answers": dict(st.session_state.selected_answers),
        "flagged_questions": sorted(st.session_state.flagged_questions),
        "flagged_count": len(st.session_state.flagged_questions)
    }

    st.session_state.quiz_history.insert(0, history_entry)
    st.session_state.history_review = None
    st.session_state.page = "Review"
