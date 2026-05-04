import streamlit as st
import plotly.graph_objects as go
from api_client import get_user_mastery, get_mastery_history 

def show_progress():
    # Authentication Check
    if not st.session_state.get("token"):
        st.switch_page("pages/testpages/login.py")
        
    st.title("Learning Progress & Mastery")
    st.divider()

    # 1. FETCH LIVE DATA FROM DB
    with st.spinner("Loading your progress..."):
        mastery_data = get_user_mastery()
        history_data = get_mastery_history() 

    # 2. FOCAL POINT: TOPIC MASTERY
    st.header("🎯 Current Topic Mastery")
    
    if not mastery_data:
        st.info("No topic data available yet. Complete some quizzes to see your mastery!")
    else:
        # Display mastery in neat columns (3 per row)
        cols = st.columns(3)
        for idx, topic in enumerate(mastery_data):
            col = cols[idx % 3]
            with col:
                pct = topic.get("mastery_percentage", 0.0)
                st.metric(
                    label=topic.get("topic_name", "Unknown Topic"), 
                    value=f"{pct}%"
                )
                
                # st.progress requires a float strictly between 0.0 and 1.0
                progress_float = min(max(pct / 100.0, 0.0), 1.0)
                st.progress(progress_float, text=f"{topic.get('total_correct', 0)}/{topic.get('total_attempted', 0)} correct")
                st.write("") # Spacer

    st.divider()

    # 3. OVER TIME: TOPIC PROGRESSION CHARTS
    st.header("📈 Topic Progress Over Time")
    
    if not history_data:
        st.info("No historical data yet. Keep taking quizzes!")
        st.stop()

    theme = st.session_state.get("theme", "Dark") 

    for topic in history_data:
        # Only show a chart if they have answered questions across at least 2 different attempts
        if len(topic.get("history", [])) < 2:
            continue 
            
        st.subheader(f"{topic['topic_name']} Mastery")
        
        # Extract the data for Plotly
        attempt_numbers = list(range(1, len(topic["history"]) + 1))
        percentages = [point["percentage"] for point in topic["history"]]
        
        # --- PLOTLY CHART CONFIG ---
        fig = go.Figure()
        
        if theme == "Light":
            line = dict(color='navy', width=5)
            marker = dict(size=10, color='black')
            axis_font = "navy"
            tick_font = "grey"
        else:
            line = dict(color='#ADD8E6', width=5)
            marker = dict(size=10, color='white')
            axis_font = "#e5ecf6"
            tick_font = "#94a3b8"
       
        fig.add_trace(go.Scatter(
            x=attempt_numbers,
            y=percentages,
            mode='lines+markers',
            line=line,
            marker=marker,
            hovertemplate='Attempt %{x}: %{y}% Mastery<extra></extra>'
        ))

        fig.update_layout(
            xaxis=dict(
                title=dict(text="Attempts Involving This Topic", font=dict(color=axis_font, size=14)),
                tickfont=dict(color=tick_font),
                dtick=1
            ),
            yaxis=dict(
                title=dict(text="Cumulative Mastery %", font=dict(color=axis_font, size=14)),
                tickfont=dict(color=tick_font),
                range=[0, 105], # Slightly above 100 so the top marker isn't cut off
                dtick=10
            ),
            height=350,
            template="simple_white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
        # --- RENDER UI ---
        col1, col2 = st.columns([2, 1])  
        with col1:
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:   
            st.write("") # Padding to push metrics down
            st.write("") 
            
            last = percentages[-1]
            previous = percentages[-2]
            max_score = max(percentages)
     
            if last > previous:
                st.success("📈 Mastery Increasing!")
            elif last < previous:
                st.error("📉 Mastery Dropped.")
            else:
                st.info("➖ Mastery Maintained.")

            st.markdown(f'<div style="font-size:24px;">Current Mastery: **{last}%**</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:gray; font-size:16px;">Peak Mastery: {max_score}%</div>', unsafe_allow_html=True)
            
        st.divider()

show_progress()