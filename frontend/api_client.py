import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def api(method: str, endpoint: str, auth: bool = True, **kwargs):
    # central API caller that attaches JWT if available
    headers = kwargs.pop("headers", {})
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        return requests.request(method, f"{API_BASE_URL}{endpoint}", headers=headers, **kwargs)
    except requests.ConnectionError:
        st.error("Cannot reach backend. Make sure FastAPI is running on port 8000.")
        return None


def login(username: str, password: str):
    # sends login request
    res = api("POST", "/login/", json={"username": username, "password": password}, auth=False)
    if res and res.status_code == 200:
        st.session_state.token = res.json()["access_token"]
        return True, None
    elif res:
        return False, res.json().get("detail", "Login failed")
    return False, "Could not reach server"


def register(username: str, password: str):
    # registers a new user
    res = api("POST", "/register/", json={"username": username, "password": password}, auth=False)
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Registration failed")
    return False, "Could not reach server"


def get_dashboard():
    # loads dashboard data for the logged-in user
    res = api("GET", "/dashboard")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load dashboard"))
    return None


def get_topic_details(topic_id: int):
    # loads detailed info for a topic
    res = api("GET", f"/topics/{topic_id}/details")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load topic details"))
    return None


def create_subject(name: str):
    # creates a new subject
    res = api("POST", "/subjects/", json={"name": name})
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Failed to create subject")
    return False, "Could not reach server"


def create_topic(name: str, subject_id: int):
    # creates a new topic under a subject
    res = api("POST", "/topics/", json={"name": name, "subject_id": subject_id})
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Failed to create topic")
    return False, "Could not reach server"


def upload_material(file_path: str, filename: str, topic_id: int):
    # uploads a PDF file to a topic
    with open(file_path, "rb") as f:
        res = api(
            "POST",
            "/materials/upload",
            data={"topic_id": topic_id},
            files={"file": (filename, f, "application/pdf")}
        )

    if res and res.status_code == 200:
        return res.json()
    else:
        print(f"Upload failed: {res.json().get('detail') if res else 'Network error'}")
        return None


def generate_quiz(name: str, difficulty_level: int, length: int, topic_ids: list[int], open_ended: bool):
    # generates a quiz from the question bank
    res = api(
        "POST",
        "/quizzes/generate",
        json={
            "name": name,
            "difficulty_level": difficulty_level,
            "length": length,
            "topic_ids": topic_ids,
            "open_ended": open_ended
        }
    )
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to generate quiz"))
    return None


def start_quiz(quiz_id: int):
    # loads quiz questions when starting a quiz
    res = api("GET", f"/quizzes/{quiz_id}/start-quiz")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to start quiz"))
    return None


def start_attempt(quiz_id: int):
    # creates a new attempt for a quiz
    res = api("POST", "/start-attempt/", json={"quiz_id": quiz_id})
    if res and res.status_code == 200:
        return res.json().get("id")
    elif res:
        st.error(res.json().get("detail", "Failed to start attempt"))
    return False


def submit_batch_answers(attempt_id: int, answers: list[dict]):
    # submits all answers at once
    res = api(
        "POST",
        "/submit-batch-answers/",
        json={"attempt_id": attempt_id, "answers": answers}
    )
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to submit batch answers"))
    return None


def finish_attempt(attempt_id: int):
    # requests graded results and AI feedback
    res = api("POST", "/finish-attempt/", json={"attempt_id": attempt_id})
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to finish attempt"))
    return None


def delete_subject(subject_id: int):
    # deletes a subject
    res = api("DELETE", f"/subjects/{subject_id}")
    if res and res.status_code == 200:
        return True
    elif res:
        st.error(res.json().get("detail", "Failed to delete subject"))
    return False


def delete_topic(topic_id: int):
    # deletes a topic
    res = api("DELETE", f"/topics/{topic_id}")
    if res and res.status_code == 200:
        return True
    elif res:
        st.error(res.json().get("detail", "Failed to delete topic"))
    return False


def delete_quiz(quiz_id: int):
    # deletes a quiz
    res = api("DELETE", f"/quizzes/{quiz_id}")
    if res and res.status_code == 200:
        return True
    elif res:
        st.error(res.json().get("detail", "Failed to delete quiz"))
    return False


def delete_material(material_id: int):
    # deletes a material file and DB entry
    res = api("DELETE", f"/materials/{material_id}")
    if res and res.status_code == 200:
        return True
    elif res:
        st.error(res.json().get("detail", "Failed to delete material"))
    return False


def get_user_attempts():
    # loads all attempts grouped by quiz
    res = api("GET", "/attempts")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load quiz attempts"))
    return None


def get_mastery_history():
    # loads mastery progression over time
    res = api("GET", "/users/me/mastery-history")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load mastery history"))
    return []


def get_user_mastery():
    # loads mastery per topic
    res = api("GET", "/users/me/mastery")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load mastery data"))
    return None
