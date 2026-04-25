import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("BACKEND_URL", "http://backend:8000")


# central API caller that attaches the JWT token when needed
def api(method: str, endpoint: str, auth: bool = True, **kwargs):
    headers = kwargs.pop("headers", {})

    if auth and st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        return requests.request(method, f"{API_BASE_URL}{endpoint}", headers=headers, **kwargs)
    except requests.ConnectionError:
        st.error("Cannot reach backend. Make sure FastAPI is running.")
        return None


# login user
def login(username: str, password: str):
    res = api("POST", "/login/", json={"username": username, "password": password}, auth=False)
    if res and res.status_code == 200:
        st.session_state.token = res.json()["access_token"]
        return True, None
    elif res:
        return False, res.json().get("detail", "Login failed")
    return False, "Could not reach server"


# register user
def register(username: str, password: str):
    res = api("POST", "/register/", json={"username": username, "password": password}, auth=False)
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Registration failed")
    return False, "Could not reach server"


# load dashboard data
def get_dashboard():
    res = api("GET", "/dashboard")
    if res and res.status_code == 200:
        return res.json()
    return None


# get topic details
def get_topic_details(topic_id: int):
    res = api("GET", f"/topics/{topic_id}/details")
    if res and res.status_code == 200:
        return res.json()
    return None


# create a subject
def create_subject(name: str):
    res = api("POST", "/subjects/", json={"name": name})
    if res and res.status_code == 200:
        return True, None
    return False, res.json().get("detail") if res else "Could not reach server"


# create a topic
def create_topic(name: str, subject_id: int):
    res = api("POST", "/topics/", json={"name": name, "subject_id": subject_id})
    if res and res.status_code == 200:
        return True, None
    return False, res.json().get("detail") if res else "Could not reach server"


# upload a PDF to a topic
def upload_material(file_path: str, filename: str, topic_id: int):
    with open(file_path, "rb") as f:
        res = api(
            "POST",
            "/materials/upload",
            files={"file": (filename, f, "application/pdf")},
            data={"topic_id": topic_id}
        )

    if res is None:
        return None

    if res.status_code != 200:
        st.error(f"Upload failed: {res.status_code} – {res.text}")
        return None

    return res.json()



# generate a quiz
def generate_quiz(name: str, difficulty_level: int, length: int, topic_ids: list[int], open_ended: bool):
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
    return None


# load quiz questions
def start_quiz(quiz_id: int):
    res = api("GET", f"/quizzes/{quiz_id}/start-quiz")
    if res and res.status_code == 200:
        return res.json()
    return None


# start a new attempt
def start_attempt(quiz_id: int):
    res = api("POST", "/start-attempt/", json={"quiz_id": quiz_id})
    if res and res.status_code == 200:
        return res.json().get("id")
    return False


# submit all answers at once
def submit_batch_answers(attempt_id: int, answers: list[dict]):
    res = api(
        "POST",
        "/submit-batch-answers/",
        json={
            "attempt_id": attempt_id,
            "answers": answers
        }
    )

    if res and res.status_code == 200:
        return res.json()
    return None


# finish attempt and get AI feedback
def finish_attempt(attempt_id: int):
    res = api("POST", "/finish-attempt/", json={"attempt_id": attempt_id})
    if res and res.status_code == 200:
        return res.json()
    return None


# delete a subject
def delete_subject(subject_id: int):
    res = api("DELETE", f"/subjects/{subject_id}")
    return res and res.status_code == 200


# delete a topic
def delete_topic(topic_id: int):
    res = api("DELETE", f"/topics/{topic_id}")
    return res and res.status_code == 200


# delete a quiz
def delete_quiz(quiz_id: int):
    res = api("DELETE", f"/quizzes/{quiz_id}")
    return res and res.status_code == 200


# delete a material
def delete_material(material_id: int):
    res = api("DELETE", f"/materials/{material_id}")
    return res and res.status_code == 200


# load all attempts grouped by quiz
def get_user_attempts():
    res = api("GET", "/attempts")
    if res and res.status_code == 200:
        return res.json()
    return None


# load mastery history over time
def get_mastery_history():
    res = api("GET", "/users/me/mastery-history")
    if res and res.status_code == 200:
        return res.json()
    return []


# load mastery per topic
def get_user_mastery():
    res = api("GET", "/users/me/mastery")
    if res and res.status_code == 200:
        return res.json()
    return None
