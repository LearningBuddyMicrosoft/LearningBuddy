# filepath: frontend/pages/home.py
import os
import tempfile
import streamlit as st

def show_home(colors):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown(f'<div style=" font-size:20px;">{st.session_state.page}</div>', unsafe_allow_html=True)
    with col2:
        st.image("logo2.png", width=350) 
    with col3:
        topic = st.session_state.get('selected_topic', '')
        if topic:
            st.markdown(f'<div style=" font-size:20px;">{topic}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:20px; color:gray;">No topic selected</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="hero-card">
        <h3 style="color:{colors["sub_text"]}; font-weight:500;">
            Welcome, {st.session_state.username}
        </h3>
        <p class="subtle">
            Upload notes, take quizzes, review answers, and track your progress.
        </p>
        <span class="stats-pill">10 Question Quiz</span>
        <span class="stats-pill">{len(st.session_state.quiz_history)} Attempts</span>
        <span class="stats-pill">{len(st.session_state.flagged_questions)} Flagged</span>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("Upload your lecture notes")
    quiz_title = st.text_input(
        "Quiz title",
        value=st.session_state.get("current_quiz_title", "Practice Quiz"),
        placeholder="e.g. Week 3 Revision",
    )
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        subject_name = st.text_input(
            "Subject",
            value=st.session_state.get("current_subject", "Uncategorized"),
            placeholder="e.g. Machine Learning",
        )
    with col_meta2:
        topic_name = st.text_input(
            "Topic",
            value=st.session_state.get("current_topic", "General"),
            placeholder="e.g. Neural Networks",
        )
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF lecture note to generate quiz questions automatically."
    )
    if uploaded_file is not None:
        if st.button("🚀 Generate Quiz from PDF", use_container_width=True):
            from backend.app.pdf_processor import generate_quiz_from_pdf
            st.session_state.current_quiz_title = quiz_title.strip() or "Practice Quiz"
            st.session_state.current_subject = subject_name.strip() or "Uncategorized"
            st.session_state.current_topic = topic_name.strip() or "General"
            st.session_state.questions = None
            st.session_state.q_index = 0
            from frontend.pages.helpers import reset_quiz
            reset_quiz()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            with st.spinner("Reading PDF and generating questions..."):
                try:
                    generated = generate_quiz_from_pdf(tmp_path, num_questions=10)
                except Exception as e:
                    st.error(f"Error generating quiz: {e}")
                    generated = []
            os.unlink(tmp_path)
            if not generated:
                st.error("Could not generate enough valid questions from this PDF.")
            else:
                st.session_state.questions = generated
                st.session_state.q_index = 0
                reset_quiz()
                st.session_state.page = "Quiz"
                st.rerun()
                n_generated = len(generated)
                if n_generated == 0:
                    st.error("Could not generate any questions from this PDF. Try a different file or ensure it contains selectable text.")
                else:
                    st.success(f"Generated {n_generated} question{'s' if n_generated > 1 else ''} from the uploaded PDF.")
                    st.session_state.questions = generated
                    st.session_state.q_index = 0
                    reset_quiz()
                    st.session_state.page = "Quiz"
                    st.rerun()