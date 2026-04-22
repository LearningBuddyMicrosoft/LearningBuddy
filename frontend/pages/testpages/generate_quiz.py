import streamlit as st
from api_client import get_dashboard, generate_quiz, start_quiz, start_attempt

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Generate Quiz – Learning Buddy", page_icon="🎓", layout="centered")

st.markdown("""
<style>
.generate-hero {
    padding: 1.3rem 1.4rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}
.generate-hero h1 {
    margin: 0;
    font-size: 1.9rem;
    line-height: 1.1;
}
.generate-hero p {
    margin: 0.45rem 0 0 0;
    color: #cbd5e1;
    font-size: 1rem;
}
.form-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 1rem 1rem 0.9rem 1rem;
    border: 1px solid rgba(15,23,42,0.08);
    box-shadow: 0 10px 24px rgba(15,23,42,0.07);
    margin-bottom: 1rem;
}
.summary-card {
    background: #0f172a;
    color: white;
    border-radius: 18px;
    padding: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
    margin-top: 1rem;
}
.summary-pill {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    margin: 0.15rem 0.35rem 0.15rem 0;
    border-radius: 999px;
    background: #1e293b;
    color: #e5e7eb;
    font-size: 0.85rem;
    border: 1px solid rgba(255,255,255,0.08);
}
div.stButton > button,
div[data-testid="stFormSubmitButton"] > button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🎓 Learning Buddy")
    st.caption("Choose topics, tune difficulty, and generate a quiz from your learning materials.")
    st.divider()

    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

    if st.button("📚 Manage Subjects", use_container_width=True):
        st.switch_page("pages/testpages/manage.py")

    st.divider()

    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.markdown("""
<div class="generate-hero">
    <h1>Generate a Quiz</h1>
    <p>Select your topics, set the difficulty and length, and let Learning Buddy build a tailored quiz for you.</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=30)
def load_dashboard():
    return get_dashboard()

dashboard = load_dashboard()
subjects = dashboard.get("subjects", []) if dashboard else []
all_topics = [t for s in subjects for t in s.get("topics", [])]

if not all_topics:
    st.warning("You need at least one topic before generating a quiz.")
    if st.button("Go to Manage"):
        st.switch_page("pages/testpages/manage.py")
    st.stop()

topic_options = {t["name"]: t["id"] for t in all_topics}

st.markdown('<div class="form-card">', unsafe_allow_html=True)

with st.form("generate_quiz_form"):
    quiz_name = st.text_input("Quiz name", placeholder="e.g. Week 3 Revision")

    selected_topic_names = st.multiselect(
        "Topics to include",
        options=list(topic_options.keys()),
        help="Select one or more topics. Questions will be grounded in their uploaded materials.",
        placeholder="Choose one or more topics",
    )

    col1, col2 = st.columns(2)
    with col1:
        difficulty = st.slider(
            "Difficulty level",
            min_value=1,
            max_value=5,
            value=3,
            help="1 = Easy · 5 = Hard",
        )
    with col2:
        length = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
        )

    open_ended = st.toggle(
        "Include open-ended questions",
        value=False,
        help="Mix free-text questions in alongside multiple-choice.",
    )

    submitted = st.form_submit_button("Generate Quiz", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="summary-card">
        <h3 style="margin-top:0;">Quiz Preview</h3>
        <p style="color:#cbd5e1; margin-bottom:0.75rem;">
            Here’s what your current setup looks like before generation.
        </p>
        <p><strong>Name:</strong> {quiz_name.strip() if quiz_name else "Not set yet"}</p>
        <p><strong>Difficulty:</strong> {difficulty} / 5</p>
        <p><strong>Questions:</strong> {int(length)}</p>
        <p><strong>Open-ended:</strong> {"Yes" if open_ended else "No"}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if selected_topic_names:
    pills = "".join([f'<span class="summary-pill">{name}</span>' for name in selected_topic_names])
    st.markdown(pills, unsafe_allow_html=True)
else:
    st.caption("No topics selected yet.")

if submitted:
    if not quiz_name.strip():
        st.warning("Please give your quiz a name.")
        st.stop()

    if not selected_topic_names:
        st.warning("Select at least one topic.")
        st.stop()

    topic_ids = [topic_options[name] for name in selected_topic_names]

    with st.spinner("Generating your quiz... this may take a moment."):
        quiz = generate_quiz(
            name=quiz_name.strip(),
            difficulty_level=int(difficulty),
            length=int(length),
            topic_ids=topic_ids,
            open_ended=open_ended,
        )

    if not quiz:
        st.stop()

    quiz_id = quiz["id"]
    st.success(f"Quiz '{quiz.get('name', quiz_name)}' generated successfully.")

    with st.spinner("Preparing your quiz..."):
        quiz_detail = start_quiz(quiz_id)
        attempt_id = start_attempt(quiz_id)

    if not quiz_detail or not attempt_id:
        st.error("Quiz was generated but could not be started. Please try again.")
        st.stop()

    st.session_state.quiz_data = quiz_detail
    st.session_state.attempt_id = attempt_id

    st.switch_page("pages/testpages/take_quiz.py")