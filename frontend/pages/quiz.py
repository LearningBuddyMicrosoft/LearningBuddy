# filepath: frontend/pages/quiz.py
import streamlit as st
from frontend.pages.helpers import submit_quiz

def get_questions():
    if st.session_state.get("questions") is not None:
        return st.session_state["questions"]
    from frontend.pages.questions import questions as static_questions
    return static_questions

def show_quiz():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("logo2.png", width=350) 
    questions = get_questions()
    if not questions:
        st.warning("No questions loaded. Please upload a PDF or use the default quiz.")
        if st.button(" Go Home"):
            st.session_state.page = "Home"
            st.rerun()
        st.stop()
    q_index = st.session_state.q_index
    total_q = len(questions)
    if q_index >= total_q:
        st.session_state.q_index = 0
        q_index = 0
    q = questions[q_index]
    st.markdown(f"""
    <div class="quiz-topbar">
        <div class="quiz-label">Question {q_index + 1} of {total_q}</div>
        <div class="quiz-meta">
            Answered: {len(st.session_state.selected_answers)} &nbsp;|&nbsp;
            Flagged: {len(st.session_state.flagged_questions)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress((q_index + 1) / total_q)
    st.markdown("<div class='quiz-card'>", unsafe_allow_html=True)
    current_answer = st.session_state.selected_answers.get(q_index, None)
    clean_options = [o.strip() for o in q["options"]]
    clean_current = current_answer.strip() if current_answer else None
    safe_index = clean_options.index(clean_current) if clean_current in clean_options else 0
    selected = st.radio(
        q["q"],
        clean_options,
        index=safe_index,
        key=f"question_radio_{q_index}"
    )
    st.session_state.selected_answers[q_index] = selected
    top_left, top_right = st.columns([1.1, 3])
    with top_left:
        is_flagged = q_index in st.session_state.flagged_questions
        if st.button("Unflag" if is_flagged else "Flag", use_container_width=True):
            if is_flagged:
                st.session_state.flagged_questions.remove(q_index)
            else:
                st.session_state.flagged_questions.add(q_index)
            st.rerun()
    with top_right:
        if is_flagged:
            st.warning("This question has been flagged for review later.")
    nav_left, nav_mid1, nav_mid2, nav_right = st.columns([1.05, 1.05, 1.05, 1.2])
    with nav_left:
        if st.button("Previous", use_container_width=True, disabled=(q_index == 0)):
            st.session_state.q_index -= 1
            st.rerun()
    with nav_mid1:
        if q_index < total_q - 1:
            if st.button("Next ➡", use_container_width=True):
                st.session_state.q_index += 1
                st.rerun()
        else:
            if st.button("✅ Submit Quiz", use_container_width=True):
                submit_quiz(questions)
                st.rerun()
    with nav_mid2:
        if st.button("Review Now", use_container_width=True):
            submit_quiz(questions)
            st.rerun()
    with nav_right:
        if st.button("Exit Quiz", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)