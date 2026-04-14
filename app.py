import os
import tempfile
import streamlit as st
from frontend.pages.helpers import initialize_session_state, reset_quiz, submit_quiz
from frontend.pages.styles import get_theme_colors, apply_custom_css
from frontend.pages.progress import show_progress

st.set_page_config(
    page_title="Learning Buddy",
    page_icon="📘",
    layout="wide"
)

initialize_session_state()
colors = get_theme_colors(st.session_state.theme)
apply_custom_css(colors)

if not st.session_state.authenticated:

    if st.session_state.auth_page == "Landing":
        # st.markdown("""
        #     <div class="auth-shell">
        #         <div class="auth-top">
        #             <div class="auth-badge">📘 Learning Buddy</div>
        #             """, unsafe_allow_html=True)
        st.markdown("""
        <div style='margin-top: 70px;'>              
                <h2 style="margin-bottom:0.35rem; text-align:center">Welcome</h2>
                """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 4, 1]) 
        with col2:
            st.image("logo2.png", width=800) 

        st.markdown("""
                  <div class="auth-top">
                    <p class="subtle">
                        A smart and simple quiz platform to help you learn, review answers,
                        track progress, and revisit flagged questions.
                    </p>
                </div>
        <div style='margin-top: 30px;'>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1.2, 1])
        st.markdown('<div class="auth-buttons">', unsafe_allow_html=True)
        with c2:
            b1, spacer, b2 = st.columns([3,0.1,3])
            with b1:
                if st.button("Login", use_container_width=True):
                    st.session_state.auth_page = "Login"
                    st.session_state.auth_mode = "Login"
                    st.rerun()

            with b2:
                if st.button("Sign Up", use_container_width=True):
                    st.session_state.auth_page = "Sign Up"
                    st.session_state.auth_mode = "Sign Up"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    elif st.session_state.auth_page == "Login":
        col1,col2=st.columns(2)
        with col1:
                    st.markdown("""
                    <div class="auth-shell sign">
                        <div class="auth-top">
                            <div class="auth-badge">📘 Learning Buddy</div>
                            <h1 style="margin-bottom:0.25rem;">Login</h1>
                            <p class="subtle">Sign up to start using Learning Buddy.</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        with col2:
                    st.markdown("<div style='margin-top: 100px;'>", unsafe_allow_html=True)

                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    st.markdown("<div style='margin-top: 150px;'>", unsafe_allow_html=True)

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("⬅ Back", use_container_width=True):
                            st.session_state.auth_page = "Landing"
                            st.rerun()

                    with c2:
                        if st.button(" Login", use_container_width=True):
                            if not username.strip() or not password.strip():
                                st.warning("Please enter both username and password.")
                            elif username in st.session_state.users and st.session_state.users[username] == password:
                                st.session_state.username = username
                                st.session_state.authenticated = True
                                st.session_state.page = "Home"
                                reset_quiz()
                                st.rerun()
                            elif username not in st.session_state.users:
                                st.error("Account not found. Please sign up first.")
                            else:
                                st.error("Incorrect password.")

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.auth_page == "Sign Up":
        col1,col2=st.columns(2)
        with col1:
            st.markdown("""
            <div class="auth-shell sign">
                <div class="auth-top">
                    <div class="auth-badge"> Learning Buddy</div>
                    <h1 style="margin-bottom:0.25rem;">Create Account</h1>
                    <p class="subtle">Sign up to start using Learning Buddy.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div style='margin-top: 100px;'>", unsafe_allow_html=True)

            username = st.text_input("Username", placeholder="Choose a username")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            st.markdown("<div style='margin-top: 30px;'>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)

            with c1:
                if st.button("⬅ Back", use_container_width=True):
                    st.session_state.auth_page = "Landing"
                    st.rerun()

            with c2:

                if st.button(" Create Account", use_container_width=True):
                    if not username.strip() or not password.strip() or not confirm_password.strip():
                        st.warning("Please complete all fields.")
                    elif len(password)<8:
                        st.error("Password must be at least 8 characters.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    elif username in st.session_state.users:
                        st.error("That username already exists. Please log in instead.")
                    else:
                        st.session_state.users[username] = password
                        st.session_state.username = username
                        st.session_state.authenticated = True
                        st.session_state.page = "Home"
                        reset_quiz()
                        st.rerun()

else:
    st.markdown("<div class='main-navbar'>", unsafe_allow_html=True)

    nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

    with nav1:
        if st.button("Home", use_container_width=True):
            st.session_state.page = "Home"

    with nav2:
        if st.button("Quiz", use_container_width=True):
            st.session_state.page = "Quiz"

    with nav3:
        if st.button("Flagged", use_container_width=True):
            st.session_state.page = "Flagged"

    with nav4:
        if st.button("History", use_container_width=True):
            st.session_state.page = "History"

    with nav5:
        if st.button("Profile", use_container_width=True):
            st.session_state.page = "Profile"
    with nav6:
        if st.button("Progress",use_container_width=True):
            st.session_state.page = "Progress"

    st.markdown("</div>", unsafe_allow_html=True)

    # ── resolve questions from session state or fall back to static list ──
    def get_questions():
        if st.session_state.get("questions") is not None:
            return st.session_state["questions"]
        from frontend.pages.questions import questions as static_questions
        return static_questions

    if st.session_state.page == "Home":
        st.markdown(f"""
        <div class="hero-card">
            <h1>📘 Learning Buddy</h1>
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

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("Upload your lecture notes")

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a PDF lecture note to generate quiz questions automatically."
        )

        c1, c2, _ = st.columns([1.1, 1.1, 3])

        with c1:
            if uploaded_file is not None:
                if st.button("🚀 Generate Quiz from PDF", use_container_width=True):
                    from backend.app.pdf_processor import generate_quiz_from_pdf

                    #Reset previous quiz state
                    st.session_state.questions = None
                    st.session_state.q_index = 0
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

                    # Validate
                    if not generated:  # you can adjust minimum questions
                        st.error("Could not generate enough valid questions from this PDF.")
                    else:
                        st.session_state.questions = generated
                        st.session_state.q_index = 0       # RESET INDEX
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
        with c2:
            if st.button("View History", use_container_width=True):
                st.session_state.page = "History"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "Quiz":
        questions = get_questions()

        if not questions:
            st.warning("No questions loaded. Please upload a PDF or use the default quiz.")
            if st.button("🏠 Go Home"):
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

        # Safe index lookup — strips both sides before comparing
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
            if st.button("🚩 Unflag" if is_flagged else "🚩 Flag", use_container_width=True):
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
            if st.button("⬅ Previous", use_container_width=True, disabled=(q_index == 0)):
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
            if st.button("❌ Exit Quiz", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "Review":
        questions = get_questions()

        st.markdown(f"""
        <div class="hero-card">
            <h1>Quiz Review</h1>
            <p class="subtle">Review your performance question by question.</p>
            <span class="stats-pill">Score: {st.session_state.score}/{len(questions)}</span>
            <span class="stats-pill">Percentage: {round((st.session_state.score / len(questions)) * 100)}%</span>
            <span class="stats-pill">Flagged: {len(st.session_state.flagged_questions)}</span>
        </div>
        """, unsafe_allow_html=True)

        r1, r2, _ = st.columns([1.1, 1.1, 3])

        with r1:
            if st.button("Show All", use_container_width=True):
                st.session_state.review_mode = "All"
                st.rerun()

        with r2:
            if st.button("🚩 Show Flagged", use_container_width=True):
                st.session_state.review_mode = "Flagged"
                st.rerun()

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)

        for i, q in enumerate(questions):
            if st.session_state.review_mode == "Flagged" and i not in st.session_state.flagged_questions:
                continue

            user_answer = st.session_state.selected_answers.get(i, "No answer selected")
            correct_answer = q["answer"].strip()
            is_correct = user_answer.strip() == correct_answer
            is_flagged = i in st.session_state.flagged_questions

            box_class = "review-correct" if is_correct else "review-wrong"

            st.markdown(f"<div class='{box_class}'>", unsafe_allow_html=True)
            st.markdown(f"**Q{i+1}. {q['q']}**")
            st.markdown(f"**Your Answer:** {user_answer}")
            st.markdown(f"**Correct Answer:** {correct_answer}")
            st.markdown(f"**Result:** {'✅ Correct' if is_correct else '❌ Incorrect' }")
                
            if q.get("explanation"):
                st.markdown(f"**Why:** {q['explanation']}")

            if q.get("source"):
                st.caption(f"Source: {q['source']}")

            if is_flagged:
                st.markdown(
                    "<div class='review-flagged'><strong>🚩 Flagged:</strong> You marked this question for review.</div>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, _ = st.columns([1.1, 1.1, 3])

        with c1:
            if st.button("Retake Quiz", use_container_width=True):
                reset_quiz()
                st.session_state.page = "Quiz"
                st.rerun()

        with c2:
            if st.button("Go Home", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "Flagged":
        questions = get_questions()

        st.markdown(f"""
        <div class="hero-card">
            <h1>🚩 Flagged Questions</h1>
            <p class="subtle">View all the questions you marked as uncertain.</p>
            <span class="stats-pill">{len(st.session_state.flagged_questions)} Currently Flagged</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)

        if not st.session_state.flagged_questions:
            st.info("You have not flagged any questions yet.")
        else:
            for i in sorted(st.session_state.flagged_questions):
                q = questions[i]
                user_answer = st.session_state.selected_answers.get(i, "No answer selected")

                st.markdown(f"""
                <div class="review-flagged">
                    <strong>Q{i+1}. {q['q']}</strong><br>
                    <strong>Your Current Answer:</strong> {user_answer}<br>
                    <strong>Correct Answer:</strong> {q['answer'].strip()}
                </div>
                """, unsafe_allow_html=True)

            c1, c2, _ = st.columns([1.1, 1.1, 3])

            with c1:
                if st.button("Return to Quiz", use_container_width=True):
                    first_flagged = sorted(st.session_state.flagged_questions)[0]
                    st.session_state.q_index = first_flagged
                    st.session_state.page = "Quiz"
                    st.rerun()

            with c2:
                if st.button("Clear Flags", use_container_width=True):
                    st.session_state.flagged_questions = set()
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "History":
        st.markdown(f"""
        <div class="hero-card">
            <h1>History</h1>
            <p class="subtle">Review your previous quiz attempts, scores, and timestamps.</p>
            <span class="stats-pill">{len(st.session_state.quiz_history)} Attempts</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        if not st.session_state.quiz_history:
            st.info("No quiz attempts yet. Complete a quiz and your history will appear here.")
        else:
            for idx, attempt in enumerate(st.session_state.quiz_history, start=1):
                st.markdown(f"""
                <div style="
                    background:{colors["option_bg"]};
                    border:1px solid {colors["border"]};
                    border-radius:14px;
                    padding:0.85rem;
                    margin-bottom:0.75rem;">
                    <strong>Attempt {idx}</strong><br>
                    <strong>Score:</strong> {attempt['score']} / {attempt['total']}<br>
                    <strong>Percentage:</strong> {attempt['percentage']}%<br>
                    <strong>Completed:</strong> {attempt['timestamp']}<br>
                    <strong>Flagged Questions:</strong> {attempt['flagged_count']}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "Profile":
        st.markdown("""
        <div class="hero-card">
            <h1>👤 Profile</h1>
            <p class="subtle">Manage your account settings and theme preferences.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)

        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Theme:** {st.session_state.theme}")
        st.write(f"**Quiz Attempts:** {len(st.session_state.quiz_history)}")
        st.write(f"**Currently Flagged Questions:** {len(st.session_state.flagged_questions)}")

        c1, c2, _ = st.columns([1.1, 1.1, 3])

        with c1:
            if st.button("🌙 Toggle Dark Mode", use_container_width=True):
                st.session_state.theme = "Dark" if st.session_state.theme == "Light" else "Light"
                st.rerun()

        with c2:
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.session_state.page = "AuthLanding"
                st.session_state.auth_page = "Landing"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    elif st.session_state.page=="Progress":
        show_progress()

st.markdown("""
<div class="footer-fixed">
    Learning Buddy © 2026
</div>
""", unsafe_allow_html=True)