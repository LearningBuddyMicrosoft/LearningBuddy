import streamlit as st
import plotly.graph_objects as go
def show_progress():
    
    history=st.session_state.get("quiz_history",[])
    if not history:
        st.info("No quiz attempts yet.")
        st.stop()
        history=st.session_state.quiz_history

    attempt_numbers=list(range(1,len(history)+1))
    percentages=[attempt["percentage"] for attempt in history]

    percentages.reverse()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=attempt_numbers,
        y=percentages,
        mode='lines+markers',
        line=dict(color='navy', width=5),
        marker=dict(size=10, color='black'),
        hovertemplate='Attempt %{x}: %{y}%<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text="Quiz Progress",
            font=dict(color="black", size=24)
        ),
        xaxis=dict(
            title=dict(
                text="Attempts",
                font=dict(color="navy", size=18)
            ),
            tickfont=dict(color="grey", size=14),
            dtick=1
        ),
        yaxis=dict(
            title=dict(
                font=dict(color="navy", size=18)
            ),
            tickfont=dict(color="grey", size=14),
            range=[0, 100],
            dtick=10
    ),
        width=600,
        height=400,
        template="simple_white",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    current_index=-1
    fig.add_annotation(
    x=attempt_numbers[current_index],
    y=percentages[current_index]+10,
    text="Current",
    showarrow=False,
    ax=0,
    ay=-30,
    font=dict(color="blue", size=14)
)
    col1, col2 = st.columns(2)  
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:   
        if len(percentages) > 1:
            last = percentages[-1]
            previous = percentages[-2]
            max_score = max(percentages[:-1])
     
            if last > previous:
                st.success("📈 Better than last attempt!")
            elif last < previous:
                st.error("📉 Worse than last attempt.")
            else:
                st.info("➖ Same as last attempt.")
        else:
            last = percentages[-1]
            max_score = last
            st.info("Only one attempt recorded.")

        if last> max_score:
            st.markdown(f"<h1 style='font-size:50px; color:green;'>NEW HIGH SCORE! {last}%</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='font-size:30px; color:blue;'>Current Score: {last}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='font-size:20px; color:orange;'>High Score: {max_score}% Can you beat it?</h2>", unsafe_allow_html=True)

        history = st.session_state.get("quiz_history", [])
        if history:
            last_attempt = history[0]  # newest attempt is at index 0
            wrong_questions = last_attempt.get("wrong_questions", [])

            if wrong_questions:
                st.markdown("### *Suggested Next Topics*")
                for q in wrong_questions:
                    st.markdown(f"- {q}")
            else:
                st.markdown("🎉 All correct! No suggested topics.")
        else:
            st.info("No quiz attempts yet.")