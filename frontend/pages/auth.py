import streamlit as st
import requests
from frontend.pages.helpers import reset_quiz

# 🔗 Your FastAPI backend URL
API_URL = "http://localhost:8000"


def show_auth():
    if st.session_state.auth_page == "Landing":
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
            b1, spacer, b2 = st.columns([3, 0.1, 3])

            with b1:
                if st.button("Login", use_container_width=True):
                    st.session_state.auth_page = "Login"
                    st.rerun()

            with b2:
                if st.button("Sign Up", use_container_width=True):
                    st.session_state.auth_page = "Sign Up"
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- LOGIN ----------------
    elif st.session_state.auth_page == "Login":
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="auth-shell sign">
                <div class="auth-top">
                    <div class="auth-badge">Learning Buddy</div>
                    <h1 style="margin-bottom:0.25rem;">Login</h1>
                    <p class="subtle">Sign in to continue.</p>
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
                if st.button("Back", use_container_width=True):
                    st.session_state.auth_page = "Landing"
                    st.rerun()

            with c2:
                if st.button("Login", use_container_width=True):
                    if not username.strip() or not password.strip():
                        st.warning("Please enter both username and password.")
                    else:
                        try:
                            response = requests.post(
                                f"{API_URL}/login",
                                json={"username": username, "password": password}
                            )

                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.username = data["username"]
                                st.session_state.user_id = data["user_id"]
                                st.session_state.authenticated = True
                                st.session_state.page = "Home"
                                reset_quiz()
                                st.rerun()

                            elif response.status_code == 401:
                                st.error("Invalid username or password.")

                            else:
                                st.error("Login failed. Please try again.")

                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to backend. Is FastAPI running?")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- SIGN UP ----------------
    elif st.session_state.auth_page == "Sign Up":
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="auth-shell sign">
                <div class="auth-top">
                    <div class="auth-badge">Learning Buddy</div>
                    <h1 style="margin-bottom:0.25rem;">Create Account</h1>
                    <p class="subtle">Sign up to get started.</p>
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
                if st.button("Back", use_container_width=True):
                    st.session_state.auth_page = "Landing"
                    st.rerun()

            with c2:
                if st.button("Create Account", use_container_width=True):
                    if not username.strip() or not password.strip() or not confirm_password.strip():
                        st.warning("Please complete all fields.")

                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters.")

                    elif password != confirm_password:
                        st.error("Passwords do not match.")

                    else:
                        try:
                            response = requests.post(
                                f"{API_URL}/signup",
                                json={"username": username, "password": password}
                            )

                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.username = username
                                st.session_state.user_id = data["user_id"]
                                st.session_state.authenticated = True
                                st.session_state.page = "Topic"
                                reset_quiz()
                                st.rerun()

                            elif response.status_code == 400:
                                st.error("Username already exists.")

                            else:
                                st.error("Signup failed. Please try again.")

                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to backend. Is FastAPI running?")