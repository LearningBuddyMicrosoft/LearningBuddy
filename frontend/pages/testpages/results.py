import streamlit as st

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Results – Learning Buddy", page_icon="🎓", layout="centered")

st.markdown("""
<style>
.results-hero {
    padding: 1.25rem 1.35rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}
.results-hero h1 {
    margin: 0;
    font-size: 1.9rem;
    line-height: 1.1;
}
.results-hero p {
    margin: 0.45rem 0 0 0;
    color: #cbd5e1;
    font-size: 1rem;
}
.metric-card {
    background: #111827;
    padding: 1rem 1.1rem;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    color: white;
    margin-bottom: 1rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
}
.metric-label {
    color: #94a3b8;
    font-size: 0.92rem;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}
.feedback-card {
    background: #0f172a;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem 1.05rem;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
    color: white;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
}
.badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.88rem;
    font-weight: 700;
    margin-top: 0.6rem;
}
.action-shell {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem;
    margin-top: 0.8rem;
}
div.stButton > button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🎓 Learning Buddy")
    st.caption("Review your performance and decide what to do next.")
    st.divider()

    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

    if st.button("Take Another Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")

    st.divider()

    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

attempt_id = st.session_state.get("last_attempt_id")
quiz_name = st.session_state.get("last_quiz_name", "Quiz")
answers_count = st.session_state.get("last_answers_count", 0)

if not attempt_id:
    st.info("No completed attempt found. Take a quiz first.")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

result_data = st.session_state.get("last_quiz_result")

st.markdown(
    f"""
    <div class="results-hero">
        <h1>Quiz Complete ✅</h1>
        <p>Your attempt has been submitted and recorded successfully.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if result_data:
    score = result_data.get("score", 0)

    if score >= 80:
        badge_html = '<span class="badge" style="background:#166534; color:#dcfce7;">Excellent</span>'
    elif score >= 50:
        badge_html = '<span class="badge" style="background:#92400e; color:#fef3c7;">Good Progress</span>'
    else:
        badge_html = '<span class="badge" style="background:#991b1b; color:#fee2e2;">Needs Review</span>'

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Quiz</div>
                <p class="metric-value" style="font-size:1.35rem;">{quiz_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Final Score</div>
                <p class="metric-value">{score}</p>
                {badge_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    extra1, extra2 = st.columns(2)
    with extra1:
        st.metric("Attempt ID", attempt_id)
    with extra2:
        st.metric("Answers Submitted", answers_count)

    st.subheader("Detailed Feedback")
    st.markdown(
        f"""
        <div class="feedback-card">
            {result_data.get("feedback", "No feedback provided.")}
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    st.warning("Could not load detailed results. Please try taking the quiz again.")

st.markdown('<div class="action-shell">', unsafe_allow_html=True)
col_a, col_b = st.columns(2)

with col_a:
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

with col_b:
    if st.button("📝 Take Another Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")

st.markdown("</div>", unsafe_allow_html=True)