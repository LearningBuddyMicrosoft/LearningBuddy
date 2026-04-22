import os
import tempfile
import streamlit as st

from api_client import (
    get_dashboard,
    create_subject,
    create_topic,
    upload_material,
    get_topic_details,
    get_questions_by_topic,
)

DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Manage – Learning Buddy", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.manage-hero {
    padding: 1.3rem 1.4rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}
.manage-hero h1 {
    margin: 0;
    font-size: 1.9rem;
    line-height: 1.1;
}
.manage-hero p {
    margin: 0.45rem 0 0 0;
    color: #cbd5e1;
    font-size: 1rem;
}
.section-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 1rem 1rem 0.8rem 1rem;
    border: 1px solid rgba(15,23,42,0.08);
    box-shadow: 0 10px 24px rgba(15,23,42,0.07);
    margin-bottom: 1rem;
}
.dark-card {
    background: #0f172a;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    color: white;
    box-shadow: 0 6px 18px rgba(0,0,0,0.10);
}
.card-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}
.card-subtitle {
    color: #94a3b8;
    font-size: 0.9rem;
    margin-bottom: 0.7rem;
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
.info-box {
    background: #f8fafc;
    border: 1px solid rgba(15,23,42,0.08);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.8rem;
}
.upload-box {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 18px;
    padding: 1rem;
    margin-top: 0.5rem;
}
.question-card {
    background: #ffffff;
    border: 1px solid rgba(15,23,42,0.08);
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 4px 12px rgba(15,23,42,0.05);
}
.question-meta {
    color: #475569;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
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
    st.caption("Organise subjects, topics, and learning materials.")
    st.divider()

    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/testpages/dashboard.py")

    if st.button("📝 Generate Quiz", use_container_width=True):
        st.switch_page("pages/testpages/generate_quiz.py")

    st.divider()

    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.markdown("""
<div class="manage-hero">
    <h1>Manage Subjects & Topics</h1>
    <p>Create subjects, organise topics, upload learning materials, and inspect topic details in one place.</p>
</div>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=30)
def load_dashboard():
    return get_dashboard()


def refresh():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()


dashboard = load_dashboard()
subjects = dashboard.get("subjects", []) if dashboard else []
all_topics = [t for s in subjects for t in s.get("topics", [])]

summary1, summary2 = st.columns(2)
with summary1:
    st.metric("Subjects", len(subjects))
with summary2:
    st.metric("Topics", len(all_topics))

tab_subjects, tab_topics, tab_upload, tab_details = st.tabs(
    ["Subjects", "Topics", "Upload Material", "Topic Details"]
)

# SUBJECTS
with tab_subjects:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Create a New Subject")

    with st.form("create_subject_form"):
        subject_name = st.text_input("Subject name", placeholder="e.g. Machine Learning")
        submitted = st.form_submit_button("Create Subject", use_container_width=True)

    if submitted:
        if not subject_name.strip():
            st.warning("Please enter a subject name.")
        else:
            ok, err = create_subject(subject_name.strip())
            if ok:
                st.success(f"Subject '{subject_name}' created.")
                refresh()
            else:
                st.error(err)
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Existing Subjects")
    if not subjects:
        st.info("No subjects yet.")
    else:
        for s in subjects:
            topics = s.get("topics", [])
            st.markdown(
                f"""
                <div class="dark-card">
                    <div class="card-title">{s['name']}</div>
                    <div class="card-subtitle">Subject ID: {s['id']} · {len(topics)} topic{'s' if len(topics) != 1 else ''}</div>
                """,
                unsafe_allow_html=True,
            )

            if topics:
                pill_html = "".join(
                    [f'<span class="topic-pill">{t["name"]}</span>' for t in topics]
                )
                st.markdown(pill_html, unsafe_allow_html=True)
            else:
                st.caption("No topics yet for this subject.")

            st.markdown("</div>", unsafe_allow_html=True)

# TOPICS
with tab_topics:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Create a New Topic")

    if not subjects:
        st.warning("Create a subject first before adding topics.")
    else:
        subject_options = {s["name"]: s["id"] for s in subjects}

        with st.form("create_topic_form"):
            topic_name = st.text_input("Topic name", placeholder="e.g. Neural Networks")
            selected_subject = st.selectbox("Under subject", list(subject_options.keys()))
            submitted = st.form_submit_button("Create Topic", use_container_width=True)

        if submitted:
            if not topic_name.strip():
                st.warning("Please enter a topic name.")
            else:
                ok, err = create_topic(topic_name.strip(), subject_options[selected_subject])
                if ok:
                    st.success(f"Topic '{topic_name}' created under '{selected_subject}'.")
                    refresh()
                else:
                    st.error(err)

    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Existing Topics by Subject")
    if not subjects:
        st.info("No subjects available yet.")
    else:
        for s in subjects:
            topics = s.get("topics", [])
            with st.expander(f"{s['name']} ({len(topics)} topic{'s' if len(topics) != 1 else ''})", expanded=False):
                if not topics:
                    st.caption("No topics yet.")
                else:
                    for t in topics:
                        st.markdown(
                            f"""
                            <div class="info-box">
                                <strong>{t['name']}</strong><br>
                                <span style="color:#64748b;">Topic ID: {t['id']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# UPLOAD
with tab_upload:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Upload Lecture Material")
    st.caption("Upload a PDF and link it to a topic.")

    if not all_topics:
        st.warning("Create at least one topic before uploading materials.")
    else:
        topic_options = {f"{t['name']} (ID {t['id']})": t["id"] for t in all_topics}

        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        selected_topic_label = st.selectbox("Link to topic", list(topic_options.keys()))
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Upload Material", use_container_width=True, disabled=uploaded_file is None):
            topic_id = topic_options[selected_topic_label]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            with st.spinner("Uploading material..."):
                result = upload_material(tmp_path, uploaded_file.name, topic_id)

            os.unlink(tmp_path)

            if result:
                st.success(f"'{uploaded_file.name}' uploaded successfully.")
            else:
                st.error("Upload failed. Check backend logs.")
    st.markdown("</div>", unsafe_allow_html=True)

# DETAILS
with tab_details:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Topic Details & Questions")

    if not all_topics:
        st.info("No topics available.")
    else:
        topic_options = {f"{t['name']} (ID {t['id']})": t["id"] for t in all_topics}

        default_label = None
        if st.session_state.get("selected_topic_id"):
            for label, tid in topic_options.items():
                if tid == st.session_state["selected_topic_id"]:
                    default_label = label
                    break

        labels = list(topic_options.keys())
        selected_label = st.selectbox(
            "Select a topic",
            labels,
            index=labels.index(default_label) if default_label else 0,
        )
        topic_id = topic_options[selected_label]

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Load Topic Details", use_container_width=True):
                st.session_state["selected_topic_id"] = None
                with st.spinner("Fetching topic details..."):
                    details = get_topic_details(topic_id)

                if details:
                    st.success("Topic details loaded.")
                    st.json(details)
                else:
                    st.error("Could not load topic details.")

        with c2:
            if st.button("Load Questions", use_container_width=True):
                with st.spinner("Fetching questions..."):
                    questions = get_questions_by_topic(topic_id)

                if questions is None:
                    st.error("Failed to fetch questions from backend.")
                elif len(questions) == 0:
                    st.warning("No questions found for this topic.")
                else:
                    st.success(f"Loaded {len(questions)} questions.")

                    for idx, q in enumerate(questions, start=1):
                        options = q.get("options") or []

                        st.markdown(
                            f"""
                            <div class="question-card">
                                <strong>Question {idx}</strong><br><br>
                                <div style="font-size:1rem; font-weight:600; margin-bottom:0.7rem;">
                                    {q.get('question_text', 'No question text')}
                                </div>
                                <div class="question-meta">
                                    Difficulty: {q.get('difficulty', 'N/A')} · Type: {q.get('question_type', 'N/A')}
                                </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if options:
                            st.markdown("**Options**")
                            for opt in options:
                                st.markdown(f"- {opt}")

                        st.markdown(f"**Answer:** `{q.get('correct_answer', '')}`")
                        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)