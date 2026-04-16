# tests/seedtest.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.database import engine
from backend.app.models import User, Subject, Topic, Question
from backend.app.seed import seed_data

import streamlit as st
from sqlmodel import Session, select

# --- Setup ---
st.set_page_config(layout="wide")
st.title("Learning Platform")

# --- Sidebar Controls ---
st.sidebar.header("Controls")

if st.sidebar.button("Reset Database"):
    seed_data()
    st.sidebar.success("Database reset!")
    st.rerun()

# --- Score tracking ---
if "score" not in st.session_state:
    st.session_state.score = 0

if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.sidebar.metric("Score", st.session_state.score)

# --- Main App ---
with Session(engine) as session:

    # ================= USER =================
    users = session.exec(select(User)).all()
    user_map = {u.username: u.id for u in users}

    selected_user = st.selectbox("Select User", list(user_map.keys()))

    if selected_user:
        user_id = user_map[selected_user]

        # ================= SUBJECT =================
        subjects = session.exec(
            select(Subject).where(Subject.user_id == user_id)
        ).all()

        subject_map = {s.name: s.id for s in subjects}
        selected_subject = st.selectbox("Select Subject", list(subject_map.keys()))

        if selected_subject:
            subject_id = subject_map[selected_subject]

            # ================= TOPIC =================
            topics = session.exec(
                select(Topic).where(Topic.subject_id == subject_id)
            ).all()

            topic_map = {t.name: t.id for t in topics}
            selected_topic = st.selectbox("Select Topic", list(topic_map.keys()))

            if selected_topic:
                topic_id = topic_map[selected_topic]

                # ================= DIFFICULTY =================
                difficulty = st.selectbox("Difficulty", [1, 2, 3])

                questions = session.exec(
                    select(Question).where(
                        (Question.topic_id == topic_id) &
                        (Question.difficulty == difficulty)
                    )
                ).all()

                if not questions:
                    st.warning("No questions for this difficulty.")
                else:
                    st.subheader("Quiz")

                    answers = {}

                    # --- Render Questions ---
                    for q in questions:
                        answers[q.id] = st.radio(
                            q.question_text,
                            q.options,
                            key=f"q_{q.id}"
                        )

                    # --- Submit Quiz ---
                    if st.button("Submit Quiz"):
                        score = 0

                        for q in questions:
                            if answers[q.id] == q.correct_answer:
                                score += 1

                        st.session_state.score = score
                        st.session_state.submitted = True

                    # --- Show Results ---
                    if st.session_state.submitted:
                        st.success(
                            f"Score: {st.session_state.score} / {len(questions)}"
                        )

                        # Show correct answers
                        for q in questions:
                            if answers[q.id] == q.correct_answer:
                                st.success(f"✔ {q.question_text}")
                            else:
                                st.error(
                                    f"Incorrect: {q.question_text} - Correct: {q.correct_answer}"
                                )