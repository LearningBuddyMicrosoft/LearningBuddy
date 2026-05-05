import streamlit as st
from api_client import get_attempt_review
from pages.testpages.styles1 import apply_custom_css

apply_custom_css()

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

if "selected_attempt" not in st.session_state:
    st.warning("No attempt selected.")
    if st.button("Back to My Quizzes"):
        st.switch_page("pages/testpages/attempts.py")
    st.stop()

attempt_id = st.session_state.selected_attempt
cache_key = f"review_cache_{attempt_id}"

if cache_key not in st.session_state:
    with st.spinner("Loading attempt review..."):
        data = get_attempt_review(attempt_id)
        if data:
            st.session_state[cache_key] = data

data = st.session_state.get(cache_key)

if not data:
    st.error("Could not load attempt review.")
    if st.button("Back to My Quizzes"):
        st.switch_page("pages/testpages/attempts.py")
    st.stop()

quiz_name = data.get("quiz_name", "Quiz")
score = data.get("score", 0)
total = data.get("total", 0)
summary = data.get("summary", "")
graded_questions = data.get("graded_questions", [])
pct = round((score / total) * 100) if total > 0 else 0

st.markdown(f"""
<div class="hero-card">
    <h1>{quiz_name}</h1>
    <p class="subtle">Attempt review</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Score", f"{score} / {total}")
with col2:
    st.metric("Percentage", f"{pct}%")
with col3:
    status = "Excellent" if pct >= 80 else "Good" if pct >= 60 else "Needs Work"
    st.metric("Status", status)

if summary:
    st.markdown("<div class='section-title'>AI Feedback</div>", unsafe_allow_html=True)
    st.info(summary)

if graded_questions:
    st.markdown("<div class='section-title'>Detailed Feedback</div>", unsafe_allow_html=True)

    for i, item in enumerate(graded_questions, start=1):
        question_text = item.get("question_text", "")
        your = item.get("your_answer", "")
        correct = item.get("correct_answer", "")
        explanation = item.get("explanation", "")
        practice_tip = item.get("practice_tip", "")
        source = item.get("source", "")

        is_correct = your.strip().lower() == correct.strip().lower()
        icon = "✅" if is_correct else "❌"

        st.markdown(f"### {icon} Question {i}")
        st.markdown(f"**{question_text}**")
        
        # Spaced layout with better visual separation
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if is_correct:
                st.markdown(f"<div style='padding: 1rem; background: #d4edda; border-radius: 0.5rem; border-left: 4px solid #28a745;'><b>✓ Your Answer</b><br>{your}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding: 1rem; background: #f8d7da; border-radius: 0.5rem; border-left: 4px solid #dc3545;'><b>✗ Your Answer</b><br>{your}</div>", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"<div style='padding: 1rem; background: #d4edda; border-radius: 0.5rem; border-left: 4px solid #28a745;'><b>✓ Correct Answer</b><br>{correct}</div>", unsafe_allow_html=True)

        st.markdown("")  # Spacing
        
        if explanation:
            st.markdown(f"<div style='padding: 1rem; background: #e7f3ff; border-radius: 0.5rem; border-left: 4px solid #0066cc;'><b>📚 Explanation</b><br>{explanation}</div>", unsafe_allow_html=True)

        if practice_tip:
            st.markdown(f"<div style='padding: 1rem; background: #fff3cd; border-radius: 0.5rem; border-left: 4px solid #ffc107;'><b>💡 Pro Tip</b><br>{practice_tip}</div>", unsafe_allow_html=True)

        if source:
            st.markdown(f"<div style='padding: 0.75rem; background: #f0f0f0; border-radius: 0.3rem; font-size: 0.9em;'><b>📖 Source:</b> {source}</div>", unsafe_allow_html=True)

        st.markdown("")  # Extra spacing between questions

st.markdown("---")
if st.button("Back to My Quizzes", use_container_width=True):
    st.switch_page("pages/testpages/attempts.py")

if st.button("Go to Dashboard", use_container_width=True):
    st.switch_page("pages/testpages/dashboard.py")