import streamlit as st
from api_client import get_all_quizzes, get_dashboard, start_quiz, start_attempt

if not st.session_state.get("token"):
    st.switch_page("pages/testpages/login.py")

st.set_page_config(page_title="Select Quiz – Learning Buddy", page_icon="🎓", layout="wide")

with st.sidebar:
    if st.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.switch_page("pages/testpages/login.py")

st.title("Select a Quiz")
st.caption("Choose any quiz below to start a new attempt.")
st.divider()

DIFFICULTY_LABELS = {1: "Easy", 2: "Medium", 3: "Hard"}
COLS_PER_ROW = 3

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading quizzes…"):
    quizzes = get_all_quizzes()
    dashboard = get_dashboard()

if quizzes is None or dashboard is None:
    st.stop()

if not quizzes:
    st.info("No quizzes available yet. Generate one first!")
    if st.button("Generate a Quiz"):
        st.switch_page("pages/testpages/generate_quiz.py")
    st.stop()

# ── Build topic lookup from dashboard ────────────────────────────────────────
# { topic_id: topic_name }
topic_lookup: dict[int, str] = {
    topic["id"]: topic["name"]
    for subject in dashboard.get("subjects", [])
    for topic in subject.get("topics", [])
}

# ── Filters ───────────────────────────────────────────────────────────────────
all_topic_names = sorted(topic_lookup.values())

filter_col1, filter_col2, _ = st.columns([1, 1, 2])
with filter_col1:
    topic_filter = st.selectbox(
        "Filter by topic",
        options=["All topics"] + all_topic_names,
    )
with filter_col2:
    difficulty_filter = st.selectbox(
        "Filter by difficulty",
        options=["All", "1 – Easy", "2 – Medium", "3 – Hard"],
    )

# Resolve selected topic name back to its ID (collect all matching IDs in case
# of identically named topics across different subjects)
filtered_topic_ids: set[int] | None = None
if topic_filter != "All topics":
    filtered_topic_ids = {
        tid for tid, tname in topic_lookup.items() if tname == topic_filter
    }

selected_difficulty: int | None = None
if difficulty_filter != "All":
    selected_difficulty = int(difficulty_filter[0])

filters_active = filtered_topic_ids is not None or selected_difficulty is not None

# ── Helper: render a single quiz card ────────────────────────────────────────
def render_quiz_card(quiz: dict, col_key_suffix: str = "") -> None:
    difficulty = quiz["difficulty_level"]
    diff_label = DIFFICULTY_LABELS.get(difficulty, str(difficulty))
    highscore = quiz["highscore"]
    length = quiz["length"]

    quiz_topic_names = [
        topic_lookup[tid] for tid in quiz.get("topic_ids", []) if tid in topic_lookup
    ]
    topics_str = ", ".join(quiz_topic_names) if quiz_topic_names else "—"

    st.markdown(f"### {quiz['name']}")
    st.markdown(
        f"**Topics:** {topics_str}  \n"
        f"**Difficulty:** {diff_label} ({difficulty}/3)  \n"
        f"**Questions:** {length}  \n"
        f"**Highscore:** {highscore}/{length}"
    )

    if st.button(
        "Start Quiz",
        key=f"start_{quiz['id']}_{col_key_suffix}",
        use_container_width=True,
        type="primary",
    ):
        with st.spinner(f"Loading '{quiz['name']}'…"):
            quiz_detail = start_quiz(quiz["id"])
            attempt_id = start_attempt(quiz["id"])

        if not quiz_detail or not attempt_id:
            st.error("Could not start this quiz. Please try again.")
            st.stop()

        st.session_state.quiz_data = quiz_detail
        st.session_state.attempt_id = attempt_id
        st.switch_page("pages/testpages/take_quiz.py")

    st.divider()


# ── Helper: render a flat grid of quiz cards ─────────────────────────────────
def render_quiz_grid(quiz_list: list[dict], key_suffix: str = "") -> None:
    for row_start in range(0, len(quiz_list), COLS_PER_ROW):
        row = quiz_list[row_start : row_start + COLS_PER_ROW]
        cols = st.columns(COLS_PER_ROW, gap="medium")
        for col, quiz in zip(cols, row):
            with col:
                render_quiz_card(quiz, col_key_suffix=f"{key_suffix}_{quiz['id']}")


# ── Apply filters and render ──────────────────────────────────────────────────
if filters_active:
    # ── Filtered flat view ────────────────────────────────────────────────────
    filtered = quizzes

    if filtered_topic_ids is not None:
        filtered = [
            q for q in filtered
            if any(tid in filtered_topic_ids for tid in q.get("topic_ids", []))
        ]

    if selected_difficulty is not None:
        filtered = [q for q in filtered if q["difficulty_level"] == selected_difficulty]

    st.caption(f"{len(filtered)} quiz{'es' if len(filtered) != 1 else ''} found")
    st.divider()

    if not filtered:
        st.info("No quizzes match the selected filters.")
    else:
        render_quiz_grid(filtered, key_suffix="filtered")

else:
    # ── Default: grouped by topic ─────────────────────────────────────────────
    # Build { topic_id: [quiz, ...] } — a quiz with multiple topics appears
    # under each of those topic sections
    topic_quiz_map: dict[int, list[dict]] = {tid: [] for tid in topic_lookup}
    unassigned: list[dict] = []

    for quiz in quizzes:
        quiz_topic_ids = quiz.get("topic_ids", [])
        placed = False
        for tid in quiz_topic_ids:
            if tid in topic_quiz_map:
                topic_quiz_map[tid].append(quiz)
                placed = True
        if not placed:
            unassigned.append(quiz)

    total = len(quizzes)
    st.caption(f"{total} quiz{'es' if total != 1 else ''} available")
    st.divider()

    for tid, tname in sorted(topic_lookup.items(), key=lambda x: x[1].lower()):
        topic_quizzes = topic_quiz_map.get(tid, [])
        if not topic_quizzes:
            continue
        with st.expander(
            f"{tname}  —  {len(topic_quizzes)} quiz{'es' if len(topic_quizzes) != 1 else ''}",
            expanded=True,
        ):
            render_quiz_grid(topic_quizzes, key_suffix=f"topic_{tid}")

    if unassigned:
        with st.expander(
            f"Uncategorised  —  {len(unassigned)} quiz{'es' if len(unassigned) != 1 else ''}",
            expanded=True,
        ):
            render_quiz_grid(unassigned, key_suffix="unassigned")