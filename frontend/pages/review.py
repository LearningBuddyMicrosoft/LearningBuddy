# filepath: frontend/pages/review.py
import streamlit as st
from frontend.pages.helpers import reset_quiz

def get_questions():
    if st.session_state.get("questions") is not None:
        return st.session_state["questions"]
    from frontend.pages.questions import questions as static_questions
    return static_questions

def show_review(colors):
    review_attempt = st.session_state.get("history_review")
    if review_attempt:
        questions = review_attempt["questions"]
        selected_answers = review_attempt["selected_answers"]
        flagged_questions = set(review_attempt["flagged_questions"])
        review_score = review_attempt["score"]
    else:
        questions = get_questions()
        selected_answers = st.session_state.selected_answers
        flagged_questions = st.session_state.flagged_questions
        review_score = st.session_state.score
    st.markdown(f"""
    <div class="hero-card">
        <h1>Quiz Review</h1>
        <p class="subtle">Review your performance question by question.</p>
        <span class="stats-pill">Score: {review_score}/{len(questions)}</span>
        <span class="stats-pill">Percentage: {round((review_score / len(questions)) * 100)}%</span>
        <span class="stats-pill">Flagged: {len(flagged_questions)}</span>
    </div>
    """, unsafe_allow_html=True)
    r1, r2, _ = st.columns([1.1, 1.1, 3])
    with r1:
        if st.button("Show All", use_container_width=True):
            st.session_state.review_mode = "All"
            st.rerun()
    with r2:
        if st.button("Show Flagged", use_container_width=True):
            st.session_state.review_mode = "Flagged"
            st.rerun()
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    for i, q in enumerate(questions):
        if st.session_state.review_mode == "Flagged" and i not in flagged_questions:
            continue
        user_answer = selected_answers.get(i, "No answer selected")
        correct_answer = q["answer"].strip()
        is_correct = user_answer.strip() == correct_answer
        is_flagged = i in flagged_questions
        box_class = "review-correct" if is_correct else "review-wrong"
        st.markdown(f"<div class='{box_class}'>", unsafe_allow_html=True)
        st.markdown(f"**Q{i+1}. {q['q']}**")
        st.markdown(f"**Your Answer:** {user_answer}")
        st.markdown(f"**Correct Answer:** {correct_answer}")
        st.markdown(f"**Result:** {'Correct' if is_correct else 'Incorrect' }")
        if q.get("explanation"):
            st.markdown(f"**Why:** {q['explanation']}")
        if q.get("source"):
            st.caption(f"Source: {q['source']}")
        if is_flagged:
            st.markdown(
                "<div class='review-flagged'><strong>Flagged:</strong> You marked this question for review.</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.1, 1.1, 3])
    with c1:
        if st.button("Retake Quiz", use_container_width=True):
            if review_attempt:
                st.session_state.questions = review_attempt["questions"]
            reset_quiz()
            st.session_state.page = "Quiz"
            st.rerun()
    with c2:
        if st.button("Go Home", use_container_width=True):
            st.session_state.history_review = None
            st.session_state.page = "Home"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)