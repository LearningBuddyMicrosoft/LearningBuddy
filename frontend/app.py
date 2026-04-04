import streamlit as st

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Learning Buddy",
    page_icon="📘",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "Auth"
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "username" not in st.session_state:
    st.session_state.username = ""
if "users" not in st.session_state:
    # simple in-memory demo storage
    st.session_state.users = {}
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

# ---------------- SAMPLE QUESTIONS ----------------
questions = [
    {
        "q": "Which protocol guarantees delivery?",
        "options": ["TCP", "UDP", "HTTP", "FTP"],
        "answer": "TCP"
    },
    {
        "q": "What does HTTP stand for?",
        "options": [
            "HyperText Transfer Protocol",
            "High Transfer Text Process",
            "Hyper Transfer Tech",
            "None"
        ],
        "answer": "HyperText Transfer Protocol"
    },
    {
        "q": "Which is NOT a programming language?",
        "options": ["Python", "Java", "HTML", "C++"],
        "answer": "HTML"
    }
]

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
/* ===== App background ===== */
.stApp {
    background: linear-gradient(135deg, #edf3ff 0%, #f8fbff 45%, #e6eefc 100%);
    color: #172033;
}

/* ===== Main spacing ===== */
.block-container {
    max-width: 1200px;
    padding-top: 2rem !important;
    padding-bottom: 6rem !important;
}

/* ===== Shared shells ===== */
.nav-shell {
    background: #1f2a44;
    padding: 14px 18px;
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.08);
}

.hero-card {
    background: rgba(255,255,255,0.80);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(31, 42, 68, 0.08);
    border-radius: 24px;
    padding: 2.2rem;
    box-shadow: 0 12px 35px rgba(31, 42, 68, 0.10);
    margin-bottom: 1.5rem;
}

.content-card {
    background: rgba(255,255,255,0.90);
    border-radius: 22px;
    padding: 2rem;
    border: 1px solid rgba(31, 42, 68, 0.08);
    box-shadow: 0 10px 28px rgba(31, 42, 68, 0.10);
    margin-top: 1rem;
}

.quiz-card {
    background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
    border-radius: 22px;
    padding: 2rem;
    border: 1px solid rgba(31, 42, 68, 0.08);
    box-shadow: 0 14px 30px rgba(31, 42, 68, 0.12);
    margin-top: 1rem;
}

/* ===== Premium auth card ===== */
.auth-shell {
    max-width: 520px;
    margin: 4vh auto 0 auto;
    background: rgba(255,255,255,0.92);
    border-radius: 28px;
    padding: 2.2rem;
    border: 1px solid rgba(31, 42, 68, 0.08);
    box-shadow: 0 18px 40px rgba(31, 42, 68, 0.14);
}

.auth-top {
    text-align: center;
    margin-bottom: 1.4rem;
}

.auth-badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: #eef4ff;
    color: #2d3a5a;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.auth-sub {
    color: #5b6783;
    font-size: 1rem;
    margin-top: 0.4rem;
}

/* ===== Buttons ===== */
div.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: 1px solid transparent;
    background: linear-gradient(180deg, #2d3a5a 0%, #22304d 100%);
    color: white;
    font-weight: 600;
    padding: 0.85rem 1rem;
    font-size: 1rem;
    transition: all 0.25s ease;
    box-shadow: 0 4px 10px rgba(0,0,0,0.10);
    cursor: pointer;
}

div.stButton > button:hover {
    transform: translateY(-2px);
    border: 1px solid #ffd166;
    background: linear-gradient(180deg, #33476d 0%, #293b60 100%);
    color: #ffd166;
    box-shadow: 0 10px 22px rgba(31, 42, 68, 0.22);
}

div.stButton > button:focus {
    outline: none !important;
    box-shadow: 0 0 0 0.2rem rgba(255, 209, 102, 0.25);
}

/* ===== Inputs ===== */
div[data-baseweb="input"] > div {
    border-radius: 14px !important;
    border: 1px solid #d5dff2 !important;
    background: #f9fbff !important;
}

div[data-baseweb="input"] input {
    color: #172033 !important;
}

[data-testid="stFileUploader"] {
    background: #f7faff;
    border: 2px dashed #b9c6e3;
    border-radius: 18px;
    padding: 1rem;
}

div[role="radiogroup"] > label {
    background: #f7faff;
    padding: 0.7rem 0.9rem;
    border-radius: 12px;
    border: 1px solid #d7e0f2;
    margin-bottom: 0.65rem;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1f2a44, #4c6fff);
}

/* ===== Footer ===== */
.footer-fixed {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background: #1f2a44;
    color: #f4f7ff;
    text-align: center;
    padding: 14px 20px;
    font-size: 0.95rem;
    font-weight: 600;
    z-index: 999;
    border-top: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 -8px 20px rgba(15, 23, 42, 0.16);
}

/* ===== Hide default Streamlit chrome ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* ===== Responsive ===== */
@media (max-width: 768px) {
    .hero-card, .content-card, .quiz-card, .auth-shell {
        padding: 1.25rem;
        border-radius: 18px;
    }

    div.stButton > button {
        font-size: 0.95rem;
        padding: 0.8rem 0.7rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------- AUTH PAGE ----------------
if not st.session_state.authenticated:
    st.markdown("""
    <div class="auth-shell">
        <div class="auth-top">
            <div class="auth-badge">📘 Learning Buddy</div>
            <h1 style="margin-bottom:0.35rem;">Welcome Back</h1>
            <p class="auth-sub">Sign in or create an account to access quizzes, history, and your study profile.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # mode buttons
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        pass
    with c2:
        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            if st.button("🔐 Login", use_container_width=True):
                st.session_state.auth_mode = "Login"
        with mode_col2:
            if st.button("✨ Sign Up", use_container_width=True):
                st.session_state.auth_mode = "Sign Up"
    with c3:
        pass

    st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)

    st.subheader(st.session_state.auth_mode)

    auth_username = st.text_input("Username", placeholder="Enter your username")
    auth_password = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.session_state.auth_mode == "Sign Up":
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

        if st.button("🚀 Create Account", use_container_width=True):
            if not auth_username.strip() or not auth_password.strip() or not confirm_password.strip():
                st.warning("Please complete all fields.")
            elif auth_password != confirm_password:
                st.error("Passwords do not match.")
            elif auth_username in st.session_state.users:
                st.error("That username already exists. Please log in instead.")
            else:
                st.session_state.users[auth_username] = auth_password
                st.session_state.username = auth_username
                st.session_state.authenticated = True
                st.session_state.page = "Home"
                st.success(f"Account created successfully. Welcome, {auth_username}!")
                st.rerun()

    else:
        if st.button("➡️ Enter Learning Buddy", use_container_width=True):
            if not auth_username.strip() or not auth_password.strip():
                st.warning("Please enter both username and password.")
            elif auth_username in st.session_state.users and st.session_state.users[auth_username] == auth_password:
                st.session_state.username = auth_username
                st.session_state.authenticated = True
                st.session_state.page = "Home"
                st.success(f"Welcome back, {auth_username}!")
                st.rerun()
            elif auth_username not in st.session_state.users:
                st.error("Account not found. Please sign up first.")
            else:
                st.error("Incorrect password.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- MAIN APP AFTER LOGIN ----------------
else:
    # NAVBAR
    st.markdown("<div class='nav-shell'>", unsafe_allow_html=True)
    nav1, nav2, nav3, nav4 = st.columns(4)

    with nav1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "Home"

    with nav2:
        if st.button("📝 Quiz", use_container_width=True):
            st.session_state.page = "Quiz"

    with nav3:
        if st.button("📊 History", use_container_width=True):
            st.session_state.page = "History"

    with nav4:
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = "Profile"

    st.markdown("</div>", unsafe_allow_html=True)

    # HOME PAGE
    if st.session_state.page == "Home":
        st.markdown(f"""
        <div class="hero-card">
            <h1 style="margin-bottom:0.4rem;">📘 Learning Buddy</h1>
            <h3 style="margin-top:0; color:#44506b; font-weight:500;">
                Welcome, {st.session_state.username}
            </h3>
            <p style="color:#5b6783; font-size:1.05rem; margin-top:0.8rem;">
                Upload notes, generate quizzes, and track your learning progress in one place.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.subheader("Upload your lecture notes")
        st.file_uploader("Choose a file", type=["pdf", "docx", "txt", "pptx"])

        c1, c2, c3 = st.columns([1.2, 1, 2.2])
        with c1:
            if st.button("🚀 Start Quiz", use_container_width=True):
                st.session_state.page = "Quiz"
                st.session_state.q_index = 0
                st.session_state.score = 0
        st.markdown("</div>", unsafe_allow_html=True)

    # QUIZ PAGE
    elif st.session_state.page == "Quiz":
        q_index = st.session_state.q_index
        total_q = len(questions)

        if q_index < total_q:
            q = questions[q_index]

            st.markdown("""
            <div class="hero-card">
                <h1 style="margin-bottom:0.3rem;">📝 Quiz Mode</h1>
                <p style="color:#5b6783; font-size:1.05rem; margin:0;">
                    Test your knowledge and track your progress.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='quiz-card'>", unsafe_allow_html=True)
            st.subheader(f"Question {q_index + 1} of {total_q}")
            st.progress((q_index + 1) / total_q)

            selected = st.radio(
                q["q"],
                q["options"],
                key=f"question_{q_index}"
            )

            col_a, col_b, col_c = st.columns([1.2, 1.2, 3])
            with col_a:
                if st.button("➡️ Next", use_container_width=True):
                    if selected == q["answer"]:
                        st.session_state.score += 1

                    if q_index + 1 < total_q:
                        st.session_state.q_index += 1
                    else:
                        st.session_state.page = "Result"
                    st.rerun()

            with col_b:
                if st.button("🏠 Exit Quiz", use_container_width=True):
                    st.session_state.page = "Home"
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # RESULT PAGE
    elif st.session_state.page == "Result":
        st.markdown("""
        <div class="hero-card">
            <h1 style="margin-bottom:0.3rem;">🎉 Quiz Complete</h1>
            <p style="color:#5b6783; font-size:1.05rem; margin:0;">
                Great work. Here is your final result.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.metric("Your Score", f"{st.session_state.score} / {len(questions)}")

        c1, c2, c3 = st.columns([1.3, 1.3, 3])
        with c1:
            if st.button("🔁 Retake Quiz", use_container_width=True):
                st.session_state.q_index = 0
                st.session_state.score = 0
                st.session_state.page = "Quiz"
                st.rerun()

        with c2:
            if st.button("🏠 Go Home", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # HISTORY PAGE
    elif st.session_state.page == "History":
        st.markdown("""
        <div class="hero-card">
            <h1 style="margin-bottom:0.3rem;">📊 History</h1>
            <p style="color:#5b6783; font-size:1.05rem; margin:0;">
                Review your past quiz activity and performance.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.info("Past quiz results will appear here once connected to saved user data.")
        st.markdown("</div>", unsafe_allow_html=True)

    # PROFILE PAGE
    elif st.session_state.page == "Profile":
        st.markdown("""
        <div class="hero-card">
            <h1 style="margin-bottom:0.3rem;">👤 Profile</h1>
            <p style="color:#5b6783; font-size:1.05rem; margin:0;">
                Manage your account and learning streak.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.write(f"**Username:** {st.session_state.username}")
        st.write("**Streak:** 3 days")
        st.write("**Status:** Active learner")

        c1, c2, c3 = st.columns([1.2, 1.2, 3])
        with c1:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.session_state.page = "Auth"
                st.rerun()

        with c2:
            if st.button("🏠 Back Home", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("""
<div class="footer-fixed">
    Learning Buddy © 2026
</div>
""", unsafe_allow_html=True)