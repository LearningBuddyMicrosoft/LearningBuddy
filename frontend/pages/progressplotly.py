import streamlit as st
import plotly.graph_objects as go

def show_progress():
    history = st.session_state.get("quiz_history", [])
    if not history:
        st.info("No quiz attempts yet.")
        st.stop()

    # Attempt numbers and scores
    attempt_numbers = list(range(1, len(history) + 1))
    percentages = [attempt["percentage"] for attempt in history]

    # Reverse so newest is at the right
    attempt_numbers.reverse()
    percentages.reverse()

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=attempt_numbers,
        y=percentages,
        mode='lines+markers',
        line=dict(color='royalblue', width=3),
        marker=dict(size=10, color='red'),
        hovertemplate='Attempt %{x}: %{y}%<extra></extra>'
    ))

    # Layout styling
    fig.update_layout(
        title="Quiz Progress Over Time",
        xaxis_title="Attempt Number",
        yaxis_title="Score (%)",
        yaxis=dict(range=[0, 100], dtick=10),
        xaxis=dict(dtick=1),
        width=600,  # adjust width
        height=400, # adjust height
        template="plotly_white"
    )

    # Display the figure in Streamlit
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    # Stats and high scores
    with col2:
        last = percentages[-1]
        previous = percentages[-2] if len(percentages) > 1 else last
        max_score = max(percentages)

        if last > max_score:
            st.markdown(f"<h1 style='font-size:70px; color:green;'>NEW HIGH SCORE! {last}%</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='font-size:50px; color:blue;'>Current Score: {last}% Can you beat it?</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='font-size:30px; color:orange;'>High Score: {max_score}%</h2>", unsafe_allow_html=True)

        # Compare last attempt to previous
        if last > previous:
            st.success("📈 Better than last attempt!")
        elif last < previous:
            st.error("📉 Worse than last attempt.")
        else:
            st.info("➖ Same as last attempt.")

        # Suggested next topics
        st.markdown("### Suggested Next Topics:")
        wrong_questions = history[-1].get("wrong_questions", [])
        if wrong_questions:
            for q in wrong_questions:
                st.markdown(f"- {q}")
        else:
            st.markdown("🎉 All correct! No suggested topics.")