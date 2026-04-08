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
import os
import tempfile
import requests
import streamlit as st
from frontend.pages.helpers import initialize_session_state, reset_quiz, submit_quiz
from frontend.pages.styles import get_theme_colors, apply_custom_css

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Learning Buddy",
    page_icon="📘",
    layout="wide"
)

initialize_session_state()

if "token" not in st.session_state:
    st.session_state.token = None
if "default_topic_id" not in st.session_state:
    st.session_state.default_topic_id = None

colors = get_theme_colors(st.session_state.theme)
apply_custom_css(colors)


# ── BACKEND HELPERS ────────────────────────────────────────────────────────────

def api(method: str, endpoint: str, auth: bool = True, **kwargs):
    """Central API caller — attaches JWT automatically."""
    headers = kwargs.pop("headers", {})
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        res = requests.request(method, f"{API_BASE_URL}{endpoint}", headers=headers, **kwargs)
        return res
    except requests.ConnectionError:
        st.error("Cannot reach backend. Make sure FastAPI is running on port 8000.")
        return None


def login(username: str, password: str):
    """POST /login/ and store token."""
    res = api("POST", "/login/", auth=False, json={"username": username, "password": password})
    if res and res.status_code == 200:
        st.session_state.token = res.json()["access_token"]
        return True, None
    elif res:
        return False, res.json().get("detail", "Login failed.")
    return False, "Could not reach server."


def register(username: str, password: str):
    """POST /register/."""
    res = api("POST", "/register/", auth=False, json={"username": username, "password": password})
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Registration failed.")
    return False, "Could not reach server."


def get_dashboard():
    """GET /dashboard — returns user data including attempts and subjects."""
    res = api("GET", "/dashboard")
    if res and res.status_code == 200:
        return res.json()
    return None


def ensure_default_topic():
    """
    Makes sure the user has a default subject + topic for quick PDF uploads.
    Creates them on the backend if they don't exist yet, and stores the topic_id.
    """
    if st.session_state.default_topic_id:
        return st.session_state.default_topic_id

    dashboard = get_dashboard()
    if not dashboard:
        return None

    subjects = dashboard.get("subjects", [])
    default_subject = next((s for s in subjects if s["name"] == "Quick Quizzes"), None)

    if not default_subject:
        res = api("POST", "/subjects/", json={"name": "Quick Quizzes"})
        if not res or res.status_code != 200:
            return None
        default_subject = res.json()

    subject_id = default_subject["id"]
    topics = default_subject.get("topics", [])
    default_topic = next((t for t in topics if t["name"] == "Uploaded Notes"), None)

    if not default_topic:
        res = api("POST", "/topics/", json={"subject_id": subject_id, "name": "Uploaded Notes"})
        if not res or res.status_code != 200:
            return None
        default_topic = res.json()

    st.session_state.default_topic_id = default_topic["id"]
    return st.session_state.default_topic_id


def upload_material_to_backend(file_path: str, filename: str, topic_id: int):
    """POST /materials/upload — sends the PDF to the backend for storage."""
    with open(file_path, "rb") as f:
        res = api(
            "POST",
            "/materials/upload",
            files={"file": (filename, f, "application/pdf")},
            data={"topic_id": topic_id}
        )
    return res and res.status_code == 200


def get_questions():
    """Returns AI-generated questions from session state, or falls back to static list."""
    if st.session_state.get("questions") is not None:
        return st.session_state["questions"]
    from frontend.pages.questions import questions as static_questions
    return static_questions


# ── AUTH PAGES ─────────────────────────────────────────────────────────────────

if not st.session_state.authenticated:

    if st.session_state.auth_page == "Landing":
        st.markdown("""
        <div class="auth-shell">
            <div class="auth-top">
                <div class="auth-badge">📘 Learning Buddy</div>
                <h1 style="margin-bottom:0.35rem;">Welcome</h1>
                <p class="subtle">
                    A smart and simple quiz platform to help you learn, review answers,
                    track progress, and revisit flagged questions.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1.2, 1])
        with c2:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🔐 Login", use_container_width=True):
                    st.session_state.auth_page = "Login"
                    st.session_state.auth_mode = "Login"
                    st.rerun()
            with b2:
                if st.button("✨ Sign Up", use_container_width=True):
                    st.session_state.auth_page = "Sign Up"
                    st.session_state.auth_mode = "Sign Up"
                    st.rerun()

    elif st.session_state.auth_page == "Login":
        st.markdown("""
        <div class="auth-shell">
            <div class="auth-top">
                <div class="auth-badge">📘 Learning Buddy</div>
                <h1 style="margin-bottom:0.25rem;">Login</h1>
                <p class="subtle">Enter your account details to continue.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.auth_page = "Landing"
                st.rerun()
        with c2:
            if st.button("➡️ Login", use_container_width=True):
                if not username.strip() or not password.strip():
                    st.warning("Please enter both username and password.")
                else:
                    success, error = login(username.strip(), password.strip())
                    if success:
                        st.session_state.username = username.strip()
                        st.session_state.authenticated = True
                        st.session_state.page = "Home"
                        reset_quiz()
                        st.rerun()
                    else:
                        if "Invalid" in (error or ""):
                            st.error("Incorrect username or password.")
                        else:
                            st.error(error or "Login failed.")

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.auth_page == "Sign Up":
        st.markdown("""
        <div class="auth-shell">
            <div class="auth-top">
                <div class="auth-badge">📘 Learning Buddy</div>
                <h1 style="margin-bottom:0.25rem;">Create Account</h1>
                <p class="subtle">Sign up to start using Learning Buddy.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.auth_page = "Landing"
                st.rerun()
        with c2:
            if st.button("🚀 Create Account", use_container_width=True):
                if not username.strip() or not password.strip() or not confirm_password.strip():
                    st.warning("Please complete all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, error = register(username.strip(), password.strip())
                    if success:
                        # Auto-login after registration
                        logged_in, login_error = login(username.strip(), password.strip())
                        if logged_in:
                            st.session_state.username = username.strip()
                            st.session_state.authenticated = True
                            st.session_state.page = "Home"
                            reset_quiz()
                            st.rerun()
                        else:
                            st.error(login_error or "Registered but could not log in.")
                    else:
                        if "already" in (error or "").lower():
                            st.error("That username already exists. Please log in instead.")
                        else:
                            st.error(error or "Registration failed.")

        st.markdown("</div>", unsafe_allow_html=True)


# ── AUTHENTICATED APP ──────────────────────────────────────────────────────────

else:
    st.markdown("<div class='main-navbar'>", unsafe_allow_html=True)

    nav1, nav2, nav3, nav4, nav5 = st.columns(5)
    with nav1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "Home"
    with nav2:
        if st.button("📝 Quiz", use_container_width=True):
            st.session_state.page = "Quiz"
    with nav3:
        if st.button("🚩 Flagged", use_container_width=True):
            st.session_state.page = "Flagged"
    with nav4:
        if st.button("📊 History", use_container_width=True):
            st.session_state.page = "History"
    with nav5:
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = "Profile"

    st.markdown("</div>", unsafe_allow_html=True)

    # ── HOME ──────────────────────────────────────────────────────────────────

    if st.session_state.page == "Home":
        dashboard = get_dashboard()
        attempt_count = len(dashboard.get("attempts", [])) if dashboard else len(st.session_state.quiz_history)

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
            <span class="stats-pill">{attempt_count} Attempts</span>
            <span class="stats-pill">{len(st.session_state.flagged_questions)} Flagged</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("Upload your lecture notes")

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a PDF lecture note to generate quiz questions with Phi-3.5."
        )

        c1, c2, _ = st.columns([1.1, 1.1, 3])

        with c1:
            if uploaded_file is not None:
                if st.button("🚀 Generate Quiz from PDF", use_container_width=True):
                    from backend.app.pdf_processor import generate_quiz_from_pdf

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    # Upload material to backend for persistent storage
                    with st.spinner("Saving material to backend..."):
                        topic_id = ensure_default_topic()
                        if topic_id:
                            uploaded = upload_material_to_backend(
                                tmp_path, uploaded_file.name, topic_id
                            )
                            if not uploaded:
                                st.warning("Material could not be saved to backend — quiz will still generate.")
                        else:
                            st.warning("Could not reach backend to save material — quiz will still generate.")

                    # Generate questions locally with Ollama
                    with st.spinner("Generating questions with Phi-3.5 via Ollama..."):
                        try:
                            generated = generate_quiz_from_pdf(tmp_path, num_questions=10)
                        except Exception as e:
                            st.error(f"Question generation failed: {e}")
                            generated = []

                    os.unlink(tmp_path)

                    if not generated or len(generated) < 3:
                        st.error("Could not generate enough valid questions. Try a different PDF.")
                    else:
                        st.session_state.questions = generated
                        st.session_state.q_index = 0
                        reset_quiz()
                        st.session_state.page = "Quiz"
                        st.rerun()
            else:
                if st.button("🚀 Start Quiz (default questions)", use_container_width=True):
                    st.session_state.questions = None
                    st.session_state.q_index = 0
                    reset_quiz()
                    st.session_state.page = "Quiz"
                    st.rerun()

        with c2:
            if st.button("📊 View History", use_container_width=True):
                st.session_state.page = "History"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── QUIZ ──────────────────────────────────────────────────────────────────

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
            if st.button("📋 Review Now", use_container_width=True):
                submit_quiz(questions)
                st.rerun()
        with nav_right:
            if st.button("❌ Exit Quiz", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── REVIEW ────────────────────────────────────────────────────────────────

    elif st.session_state.page == "Review":
        questions = get_questions()

        st.markdown(f"""
        <div class="hero-card">
            <h1>✅ Quiz Review</h1>
            <p class="subtle">Review your performance question by question.</p>
            <span class="stats-pill">Score: {st.session_state.score}/{len(questions)}</span>
            <span class="stats-pill">Percentage: {round((st.session_state.score / len(questions)) * 100)}%</span>
            <span class="stats-pill">Flagged: {len(st.session_state.flagged_questions)}</span>
        </div>
        """, unsafe_allow_html=True)

        r1, r2, _ = st.columns([1.1, 1.1, 3])
        with r1:
            if st.button("📄 Show All", use_container_width=True):
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
            st.markdown(f"**Result:** {'✅ Correct' if is_correct else '❌ Incorrect'}")

            if q.get("explanation"):
                st.markdown(f"**Why:** {q['explanation']}")
            if q.get("source"):
                st.caption(f"Source: {q['source']}")
            if is_flagged:
                st.markdown(
                    "<div class='review-flagged'><strong>🚩 Flagged:</strong> You marked this for review.</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, _ = st.columns([1.1, 1.1, 3])
        with c1:
            if st.button("🔁 Retake Quiz", use_container_width=True):
                reset_quiz()
                st.session_state.page = "Quiz"
                st.rerun()
        with c2:
            if st.button("🏠 Go Home", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── FLAGGED ───────────────────────────────────────────────────────────────

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
                if st.button("📝 Return to Quiz", use_container_width=True):
                    st.session_state.q_index = sorted(st.session_state.flagged_questions)[0]
                    st.session_state.page = "Quiz"
                    st.rerun()
            with c2:
                if st.button("🧹 Clear Flags", use_container_width=True):
                    st.session_state.flagged_questions = set()
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── HISTORY ───────────────────────────────────────────────────────────────

    elif st.session_state.page == "History":
        dashboard = get_dashboard()
        backend_attempts = dashboard.get("attempts", []) if dashboard else []

        st.markdown(f"""
        <div class="hero-card">
            <h1>📊 History</h1>
            <p class="subtle">Review your previous quiz attempts, scores, and timestamps.</p>
            <span class="stats-pill">{len(backend_attempts)} Attempts</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)

        if not backend_attempts and not st.session_state.quiz_history:
            st.info("No quiz attempts yet. Complete a quiz and your history will appear here.")

        # Backend attempts (persistent across sessions)
        if backend_attempts:
            st.markdown("##### From backend")
            for idx, attempt in enumerate(reversed(backend_attempts), start=1):
                score = attempt.get("score", 0)
                feedback = attempt.get("feedback", "")
                date = attempt.get("date", "Unknown")
                quiz_id = attempt.get("quiz_id", "—")
                st.markdown(f"""
                <div style="
                    background:{colors["option_bg"]};
                    border:1px solid {colors["border"]};
                    border-radius:14px;
                    padding:0.85rem;
                    margin-bottom:0.75rem;">
                    <strong>Attempt {idx}</strong><br>
                    <strong>Score:</strong> {score}<br>
                    <strong>Feedback:</strong> {feedback}<br>
                    <strong>Date:</strong> {date}<br>
                    <strong>Quiz ID:</strong> {quiz_id}
                </div>
                """, unsafe_allow_html=True)

        # Local session attempts (AI-generated quizzes from this session)
        if st.session_state.quiz_history:
            st.markdown("##### From this session")
            for idx, attempt in enumerate(st.session_state.quiz_history, start=1):
                st.markdown(f"""
                <div style="
                    background:{colors["option_bg"]};
                    border:1px solid {colors["border"]};
                    border-radius:14px;
                    padding:0.85rem;
                    margin-bottom:0.75rem;">
                    <strong>Session Attempt {idx}</strong><br>
                    <strong>Score:</strong> {attempt['score']} / {attempt['total']}<br>
                    <strong>Percentage:</strong> {attempt['percentage']}%<br>
                    <strong>Completed:</strong> {attempt['timestamp']}<br>
                    <strong>Flagged Questions:</strong> {attempt['flagged_count']}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── PROFILE ───────────────────────────────────────────────────────────────

    elif st.session_state.page == "Profile":
        dashboard = get_dashboard()
        subject_count = len(dashboard.get("subjects", [])) if dashboard else 0
        attempt_count = len(dashboard.get("attempts", [])) if dashboard else 0

        st.markdown("""
        <div class="hero-card">
            <h1>👤 Profile</h1>
            <p class="subtle">Manage your account settings and preferences.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)

        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Theme:** {st.session_state.theme}")
        st.write(f"**Subjects on backend:** {subject_count}")
        st.write(f"**Total quiz attempts:** {attempt_count}")
        st.write(f"**Currently flagged questions:** {len(st.session_state.flagged_questions)}")

        c1, c2, _ = st.columns([1.1, 1.1, 3])
        with c1:
            if st.button("🌙 Toggle Dark Mode", use_container_width=True):
                st.session_state.theme = "Dark" if st.session_state.theme == "Light" else "Light"
                st.rerun()
        with c2:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.token = None
                st.session_state.username = ""
                st.session_state.default_topic_id = None
                st.session_state.questions = None
                st.session_state.page = "AuthLanding"
                st.session_state.auth_page = "Landing"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ── FOOTER ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="footer-fixed">
    Learning Buddy © 2026
</div>
""", unsafe_allow_html=True)
initialize_session_state()
colors = get_theme_colors(st.session_state.theme)
apply_custom_css(colors)

if not st.session_state.authenticated:

    if st.session_state.auth_page == "Landing":
        st.markdown("""
        <div class="auth-shell">
            <div class="auth-top">
                <div class="auth-badge">📘 Learning Buddy</div>
                <h1 style="margin-bottom:0.35rem;">Welcome</h1>
                <p class="subtle">
                    A smart and simple quiz platform to help you learn, review answers,
                    track progress, and revisit flagged questions.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1.2, 1])

        with c2:
            b1, b2 = st.columns(2)

            
            with b1:
                if st.button("🔐 Login", use_container_width=True):
                    st.session_state.auth_page = "Login"
                    st.session_state.auth_mode = "Login"
                    st.rerun()

            with b2:
                if st.button("✨ Sign Up", use_container_width=True):
                    st.session_state.auth_page = "Sign Up"
                    st.session_state.auth_mode = "Sign Up"
                    st.rerun()

    elif st.session_state.auth_page == "Login":
        st.markdown("""
        <div class="auth-shell">
            <div class="auth-top">
                <div class="auth-badge">📘 Learning Buddy</div>
                <h1 style="margin-bottom:0.25rem;">Login</h1>
                <p class="subtle">Enter your account details to continue.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.auth_page = "Landing"
                st.rerun()

        with c2:
            if st.button("➡️ Login", use_container_width=True):
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
        st.markdown("""
        <div class="auth-shell">
            <div class="auth-top">
                <div class="auth-badge">📘 Learning Buddy</div>
                <h1 style="margin-bottom:0.25rem;">Create Account</h1>
                <p class="subtle">Sign up to start using Learning Buddy.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.auth_page = "Landing"
                st.rerun()

        with c2:
            if st.button("🚀 Create Account", use_container_width=True):
                if not username.strip() or not password.strip() or not confirm_password.strip():
                    st.warning("Please complete all fields.")
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
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "Home"

    with nav2:
        if st.button("📝 Quiz", use_container_width=True):
            st.session_state.page = "Quiz"

    with nav3:
        if st.button("🚩 Flagged", use_container_width=True):
            st.session_state.page = "Flagged"

    with nav4:
        if st.button("📊 History", use_container_width=True):
            st.session_state.page = "History"

    with nav5:
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = "Profile"
    with nav6:
        if st.button("📈 Progress",use_container_width=True):
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
            if st.button("📊 View History", use_container_width=True):
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
            if st.button("📋 Review Now", use_container_width=True):
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
            <h1>✅ Quiz Review</h1>
            <p class="subtle">Review your performance question by question.</p>
            <span class="stats-pill">Score: {st.session_state.score}/{len(questions)}</span>
            <span class="stats-pill">Percentage: {round((st.session_state.score / len(questions)) * 100)}%</span>
            <span class="stats-pill">Flagged: {len(st.session_state.flagged_questions)}</span>
        </div>
        """, unsafe_allow_html=True)

        r1, r2, _ = st.columns([1.1, 1.1, 3])

        with r1:
            if st.button("📄 Show All", use_container_width=True):
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
            if st.button("🔁 Retake Quiz", use_container_width=True):
                reset_quiz()
                st.session_state.page = "Quiz"
                st.rerun()

        with c2:
            if st.button("🏠 Go Home", use_container_width=True):
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
                if st.button("📝 Return to Quiz", use_container_width=True):
                    first_flagged = sorted(st.session_state.flagged_questions)[0]
                    st.session_state.q_index = first_flagged
                    st.session_state.page = "Quiz"
                    st.rerun()

            with c2:
                if st.button("🧹 Clear Flags", use_container_width=True):
                    st.session_state.flagged_questions = set()
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "History":
        st.markdown(f"""
        <div class="hero-card">
            <h1>📊 History</h1>
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
            if st.button("🚪 Logout", use_container_width=True):
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