import plotly.graph_objects as go
import streamlit as st

from api_client import get_mastery_history, get_user_mastery
from pages.testpages.styles1 import apply_custom_css, apply_progress_page_css

st.set_page_config(page_title="Progress – Learning Buddy", page_icon="🎓", layout="wide")
apply_custom_css()


def build_progress_figure(attempt_numbers, percentages):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=attempt_numbers,
            y=percentages,
            mode="lines+markers",
            line=dict(color="#7cc7ff", width=4),
            marker=dict(size=10, color="#43c6ac", line=dict(color="#d9f8ff", width=1.5)),
            hovertemplate="Attempt %{x}: %{y}% mastery<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis=dict(
            title=dict(text="Attempts involving this topic", font=dict(color="#eef4f8", size=14)),
            tickfont=dict(color="#95a6b8"),
            dtick=1,
            gridcolor="rgba(149, 166, 184, 0.18)",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="Cumulative mastery %", font=dict(color="#eef4f8", size=14)),
            tickfont=dict(color="#95a6b8"),
            range=[0, 105],
            dtick=10,
            gridcolor="rgba(149, 166, 184, 0.18)",
            zeroline=False,
        ),
        height=360,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=24, b=24),
    )
    return fig


def show_progress():
    if not st.session_state.get("token"):
        st.switch_page("pages/testpages/login.py")

    with st.sidebar:
        if st.button("Log Out", use_container_width=True):
            st.session_state.token = None
            st.switch_page("pages/testpages/login.py")

    apply_progress_page_css()

    with st.spinner("Loading your progress..."):
        mastery_data = get_user_mastery()
        history_data = get_mastery_history()

    topic_count = len(mastery_data) if mastery_data else 0
    avg_mastery = (
        round(sum(topic.get("mastery_percentage", 0.0) for topic in mastery_data) / topic_count)
        if topic_count
        else 0
    )
    strongest_topic = (
        max(mastery_data, key=lambda topic: topic.get("mastery_percentage", 0.0))
        if mastery_data
        else None
    )
    tracked_histories = [
        topic for topic in (history_data or []) if len(topic.get("history", [])) >= 2
    ]

    st.markdown("<div class='progress-shell'>", unsafe_allow_html=True)
    st.markdown(
        """
        <section class="progress-hero">
            <span class="progress-eyebrow">Progress workspace</span>
            <h1>Learning Progress & Mastery</h1>
            <p>
                Track your strongest topics, spot momentum over time, and see where a little more practice will move the needle.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    metrics = [
        ("Topics tracked", f"{topic_count}", "Subjects with mastery data"),
        ("Average mastery", f"{avg_mastery}%", "Across all tracked topics"),
        (
            "Top topic",
            strongest_topic.get("topic_name", "None") if strongest_topic else "None",
            "Your strongest area right now",
        ),
        ("Trend charts", f"{len(tracked_histories)}", "Topics with enough history to graph"),
    ]

    for col, (label, value, subtext) in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-subtext">{subtext}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div class='section-title'>Current Topic Mastery</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-copy'>A quick snapshot of how each topic is going right now.</div>",
        unsafe_allow_html=True,
    )

    if not mastery_data:
        st.info("No topic data available yet. Complete some quizzes to see your mastery.")
    else:
        mastery_cols = st.columns(3)
        for idx, topic in enumerate(mastery_data):
            with mastery_cols[idx % 3]:
                pct = topic.get("mastery_percentage", 0.0)
                progress_float = min(max(pct / 100.0, 0.0), 1.0)
                st.markdown(
                    f"""
                    <div class="mastery-card">
                        <div class="mastery-title">{topic.get("topic_name", "Unknown Topic")}</div>
                        <div class="mastery-value">{pct}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.progress(progress_float)
                st.markdown(
                    f"""
                    <div class="mastery-stats">
                        <span class="mastery-stats-label">Accuracy</span>
                        <span class="mastery-stats-value">
                            {topic.get('total_correct', 0)} / {topic.get('total_attempted', 0)} correct
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div class='mastery-copy'>Current understanding based on your recorded quiz performance.</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("<div class='section-title'>Topic Progress Over Time</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-copy'>These charts show how your cumulative mastery changes across repeated quiz attempts.</div>",
        unsafe_allow_html=True,
    )

    if not history_data:
        st.info("No historical data yet. Keep taking quizzes.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    rendered_any_chart = False
    for topic in history_data:
        if len(topic.get("history", [])) < 2:
            continue

        rendered_any_chart = True
        percentages = [point["percentage"] for point in topic["history"]]
        attempt_numbers = list(range(1, len(percentages) + 1))
        last = percentages[-1]
        previous = percentages[-2]
        max_score = max(percentages)

        if last > previous:
            trend_label = "Mastery increasing"
            trend_class = "trend-pill"
        elif last < previous:
            trend_label = "Mastery dropped"
            trend_class = "trend-pill down"
        else:
            trend_label = "Mastery maintained"
            trend_class = "trend-pill flat"

        st.markdown(
            f"""
            <div class="topic-title">{topic['topic_name']}</div>
            <div class="topic-copy">Mastery trend across your recorded attempts for this topic.</div>
            """,
            unsafe_allow_html=True,
        )

        chart_col, insight_col = st.columns([2.1, 0.95], gap="large")
        with chart_col:
            st.plotly_chart(
                build_progress_figure(attempt_numbers, percentages),
                use_container_width=True,
            )

        with insight_col:
            st.markdown(f"<span class='{trend_class}'>{trend_label}</span>", unsafe_allow_html=True)
            st.markdown("<div class='insight-stack'>", unsafe_allow_html=True)
            st.markdown("<div class='insight-label'>Current Mastery</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='insight-value'>{last}%</div>", unsafe_allow_html=True)
            st.markdown("<div class='insight-subtext'>Most recent cumulative score.</div>", unsafe_allow_html=True)
            st.markdown("<div class='insight-label'>Peak Mastery</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='insight-value'>{max_score}%</div>", unsafe_allow_html=True)
            st.markdown("<div class='insight-subtext'>Best result reached so far.</div>", unsafe_allow_html=True)
            st.markdown("<div class='insight-label'>Attempts</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='insight-value'>{len(attempt_numbers)}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='insight-subtext'>Recorded quizzes contributing to this view.</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    if not rendered_any_chart:
        st.info("You need at least two attempts on a topic before we can show a trend chart.")

    st.markdown("</div>", unsafe_allow_html=True)


show_progress()
