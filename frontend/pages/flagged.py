# filepath: frontend/pages/flagged.py
import streamlit as st

def get_questions():
    if st.session_state.get("questions") is not None:
        return st.session_state["questions"]
    from frontend.pages.questions import questions as static_questions
    return static_questions

def show_flagged():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("logo2.png", width=350) 
    questions = get_questions()
    st.markdown(f"""
    <div class="hero-card">
        <h1> Flagged Questions</h1>
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