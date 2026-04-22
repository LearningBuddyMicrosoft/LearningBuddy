import streamlit as st
from api_client import get_dashboard

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Dashboard – Learning Buddy", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.dashboard-hero {
    padding: 1.4rem 1.5rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}
.dashboard-hero h1 {
    margin: 0;
    font-size: 2rem;
    line-height: 1.1;
}
.dashboard-hero p {
    margin: 0.5rem 0 0 0;
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
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
}
.metric-label {
    font-size: 0.95rem;
    color: #94a3b8;
    margin-bottom: 0.35rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}
.section-title {
    margin-top: 0.5rem;
    margin-bottom: 0.75rem;
    font-size: 1.2rem;
    font-weight: 700;
}
.subject-card {
    background: #0f172a;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
}
.subject-title {
    color: white;
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.subject-subtitle {
    color: #94a3b8;
    font-size: 0.92rem;
    margin-bottom: 0.8rem;
}
.topic-pill {
    display: inline-block;
    padding: 0.35rem 0.7rem;
    margin: 0.15rem 0.35rem 0.15rem 0;
    border-radius: 999px;
    background: #1e293b;
    color: #e5e7eb;
    font-size: 0.85rem;
    border: 1px solid rgba(255,255,255,0.08);
}
div.stButton > button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🎓 Learning Buddy")
    st.caption("Build subjects, upload materials, and generate smarter quizzes.")
    st.divider()

    if st.button("📚 Manage Subjects", use_container_width=True):
        st.switch_page("pages/testpages/manage.py")

    if st.button("📝 Generate Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")

    st.divider()

    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.quiz_data = None
        st.session_state.attempt_id = None
        st.switch_page("pages/testpages/login.py")

data = get_dashboard()
if not data:
    st.stop()

subjects = data.get("subjects", [])
total_topics = sum(len(s.get("topics", [])) for s in subjects)

st.markdown(
    f"""
    <div class="dashboard-hero">
        <h1>Welcome back, {data['username']} 👋</h1>
        <p>Your study space is ready. Review your subjects, explore topics, and generate quizzes from your materials.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2 = st.columns(2)
with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Subjects</div>
            <p class="metric-value">{len(subjects)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Topics</div>
            <p class="metric-value">{total_topics}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

a1, a2 = st.columns(2)
with a1:
    if st.button("➕ Add Subject or Topic", use_container_width=True):
        st.switch_page("pages/testpages/manage.py")
with a2:
    if st.button("⚡ Generate a New Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")

st.markdown('<div class="section-title">Your Subjects</div>', unsafe_allow_html=True)

if not subjects:
    st.info("You have no subjects yet. Go to Manage to create your first subject and upload materials.")
    if st.button("Go to Manage"):
        st.switch_page("pages/testpages/manage.py")
    st.stop()

for subject in subjects:
    topics = subject.get("topics", [])

    st.markdown(
        f"""
        <div class="subject-card">
            <div class="subject-title">{subject['name']}</div>
            <div class="subject-subtitle">{len(topics)} topic{'s' if len(topics) != 1 else ''}</div>
        """,
        unsafe_allow_html=True,
    )

    if topics:
        pill_html = "".join(
            [f'<span class="topic-pill">{topic["name"]}</span>' for topic in topics]
        )
        st.markdown(pill_html, unsafe_allow_html=True)
    else:
        st.caption("No topics yet. Add one in the Manage page.")

    topic_cols = st.columns(3)
    for i, topic in enumerate(topics):
        with topic_cols[i % 3]:
            if st.button(f"View {topic['name']}", key=f"topic_detail_{topic['id']}"):
                st.session_state["selected_topic_id"] = topic["id"]
                st.switch_page("pages/testpages/manage.py")

    st.markdown("</div>", unsafe_allow_html=True)