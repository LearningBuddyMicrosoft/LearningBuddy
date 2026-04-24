import streamlit as st
import plotly.graph_objects as go


def show_hallucination():
    st.markdown("""
    <div class="hero-card">
        <h1>Hallucination Checker</h1>
        <p class="subtle">This page automatically evaluates the hallucination rate of the generated quiz questions.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.write("The score is calculated from the generated quiz questions and their source context. A lower score means the output is more grounded.")
    st.write("Questions with a score above 0.5 are automatically excluded from the generated quiz.")

    pdf_questions = st.session_state.get("questions")
    if not pdf_questions:
        st.info("No generated PDF quiz is available yet. Upload a PDF and generate a quiz to compute hallucination rates automatically.")
    else:
        question_scores = [q.get("hallucination_score") for q in pdf_questions if q.get("hallucination_score") is not None]
        if not question_scores:
            st.warning("No hallucination scores are available for the current quiz.")
        else:
            average_score = sum(question_scores) / len(question_scores)
            severity = "Low" if average_score < 0.3 else "Medium" if average_score < 0.7 else "High"
            color = "#2ECC71" if severity == "Low" else "#F1C40F" if severity == "Medium" else "#E74C3C"

            st.markdown(f"<div style='padding:1rem; background:{color}; color:#111; border-radius:12px; margin-top:1rem;'>Latest severity: <strong>{severity}</strong></div>", unsafe_allow_html=True)
            st.metric("Hallucination score", f"{average_score:.2f} / 1.00", delta=f"{severity}")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, len(question_scores) + 1)),
                y=question_scores,
                mode="lines+markers",
                line=dict(color="#ADD8E6", width=4),
                marker=dict(color="white", size=10),
                hovertemplate="Question %{x}: %{y:.2f}<extra></extra>"
            ))
            fig.update_layout(
                title=dict(text="Hallucination score by question", font=dict(color="#ADD8E6", size=20)),
                xaxis=dict(title="Question #", tickmode="linear", tick0=1, dtick=1),
                yaxis=dict(title="Score", range=[0, 1]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("Question details")
            for idx, q in enumerate(pdf_questions, start=1):
                score = q.get("hallucination_score")
                if score is None:
                    continue
                status = "Low" if score < 0.3 else "Medium" if score < 0.7 else "High"
                st.markdown(f"**Q{idx}.** {q['q']}  —  Score: {score:.2f} ({status})")
                with st.expander("View source context", expanded=False):
                    st.write(q.get("source", "No source text available."))

    st.markdown("</div>", unsafe_allow_html=True)