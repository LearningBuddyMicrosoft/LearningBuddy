import streamlit as st
import plotly.graph_objects as go
from pages.testpages.styles1 import apply_custom_css

apply_custom_css()

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")


def show_hallucination():
    st.markdown("""
    <div class="hero-card">
        <h1>Hallucination Checker</h1>
        <p class="subtle">Evaluates how grounded the generated quiz questions are against their source material.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.write("The score is calculated from the generated quiz questions and their source context. "
             "A lower score means the output is more grounded.")
    st.write("Questions with a score above 0.5 are automatically excluded from the generated quiz.")

    quiz_data = st.session_state.get("quiz_data")
    pdf_questions = st.session_state.get("questions")

    if not pdf_questions and quiz_data:
        questions = quiz_data.get("questions", [])
        if not questions:
            st.warning("No active quiz found. Please generate a quiz first.")
            if st.button("Generate a Quiz"):
                st.switch_page("pages/testpages/generate_quiz.py")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        st.info(
            f"ℹ️ Your quiz has **{len(questions)} question(s)**. "
            "Hallucination filtering is applied automatically during generation — "
            "any question scoring above 0.5 was removed before reaching you."
        )
        st.subheader("Question list")
        for idx, q in enumerate(questions, start=1):
            question_text = q.get("text") or q.get("question", "No question text")
            st.markdown(f"**Q{idx}.** {question_text}")
            options = q.get("options", [])
            if options:
                for opt in options:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• {opt}")

        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not pdf_questions:
        st.warning("No active quiz found. Please generate a quiz first.")
        if st.button("Generate a Quiz"):
            st.switch_page("pages/testpages/generate_quiz.py")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    question_scores = [
        q.get("hallucination_score")
        for q in pdf_questions
        if q.get("hallucination_score") is not None
    ]

    if not question_scores:
        st.warning("No hallucination scores are available for the current quiz.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    average_score = sum(question_scores) / len(question_scores)
    severity = "Low" if average_score < 0.3 else "Medium" if average_score < 0.7 else "High"
    color = "#2ECC71" if severity == "Low" else "#F1C40F" if severity == "Medium" else "#E74C3C"

    st.markdown(
        f"<div style='padding:1rem; background:{color}; color:#111; border-radius:12px; margin-top:1rem;'>"
        f"Latest severity: <strong>{severity}</strong></div>",
        unsafe_allow_html=True,
    )
    st.metric("Hallucination score", f"{average_score:.2f} / 1.00", delta=severity)

    labels = [f"Q{i}" for i in range(1, len(question_scores) + 1)]
    bar_colors = [
        "#2ECC71" if s < 0.3 else "#F1C40F" if s < 0.7 else "#E74C3C"
        for s in question_scores
    ]

    fig = go.Figure()

    fig.add_hline(
        y=0.5,
        line_dash="dash",
        line_color="rgba(255,255,255,0.4)",
        annotation_text="Exclusion threshold (0.5)",
        annotation_position="top left",
        annotation_font_color="rgba(255,255,255,0.6)",
    )

    fig.add_trace(go.Bar(
        x=labels,
        y=question_scores,
        marker_color=bar_colors,
        marker_line_color="rgba(255,255,255,0.2)",
        marker_line_width=1,
        text=[f"{s:.2f}" for s in question_scores],
        textposition="outside",
        textfont=dict(color="white", size=11),
        hovertemplate="<b>%{x}</b><br>Score: %{y:.3f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Hallucination score by question (PDF source)",
            font=dict(color="#ADD8E6", size=20),
        ),
        xaxis=dict(
            title="Question",
            tickfont=dict(color="#ADD8E6"),
            titlefont=dict(color="#ADD8E6"),
        ),
        yaxis=dict(
            title="Score",
            range=[0, 1.15],
            tickfont=dict(color="#ADD8E6"),
            titlefont=dict(color="#ADD8E6"),
            gridcolor="rgba(255,255,255,0.08)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=420,
        margin=dict(t=60, b=40, l=40, r=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Question details")
    for idx, q in enumerate(pdf_questions, start=1):
        score = q.get("hallucination_score")
        if score is None:
            continue
        status = "Low" if score < 0.3 else "Medium" if score < 0.7 else "High"
        question_text = q.get("q") or q.get("question", "")
        st.markdown(f"**Q{idx}.** {question_text}  —  Score: {score:.2f} ({status})")
        with st.expander("View source context", expanded=False):
            st.write(q.get("source", "No source text available."))

    st.markdown("</div>", unsafe_allow_html=True)


show_hallucination()