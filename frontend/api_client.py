import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

def api(method: str, endpoint: str, auth: bool = True, **kwargs):
    """Central API caller — attaches JWT automatically."""
    headers = kwargs.pop("headers", {})
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        res = requests.request(method, f"{API_BASE_URL}{endpoint}", headers=headers, **kwargs)
        return res
    except requests.ConnectionError:
        st.error("Cannot reach backend. Make sure FastAPI is running on port 8000.")
        return None

def login(username: str, password: str):
    res = api("POST", "/login/", json={"username": username, "password": password}, auth=False)
    if res and res.status_code == 200:
        st.session_state.token = res.json()["access_token"]
        return True, None
    elif res:
        return False, res.json().get("detail", "Login failed")
    return False, "Could not reach server"

def register(username: str, password: str):
    res = api("POST", "/register/", json={"username": username, "password": password}, auth=False)
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Registration failed")
    return False, "Could not reach server"

def get_dashboard():
    res = api("GET", "/dashboard")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load dashboard"))
    return None

def get_topic_details(topic_id: int):
    res = api("GET", f"/topics/{topic_id}/details")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to load topic details"))
    return None

def create_subject(name: str):
    res = api("POST", "/subjects/", json={"name": name})
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Failed to create subject")
    return False, "Could not reach server"

def create_topic(name: str, subject_id: int):
    res = api("POST", "/topics/", json={"name": name, "subject_id": subject_id})
    if res and res.status_code == 200:
        return True, None
    elif res:
        return False, res.json().get("detail", "Failed to create topic")
    return False, "Could not reach server"

def upload_material(file_path: str, filename: str, topic_id: int):
    """
    Uploads a PDF file and links it to a specific topic.
    """
    with open(file_path, "rb") as f:
        res = api(
            "POST",
            "/materials/upload",
            # data= maps directly to FastAPI's Form(...)
            data={"topic_id": topic_id}, 
            # files= maps directly to FastAPI's File(...)
            files={"file": (filename, f, "application/pdf")} 
        )
        
    if res and res.status_code == 200:
        return res.json()
    else:
        print(f"Upload failed: {res.json().get('detail') if res else 'Network error'}")
        return None
    
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
    elif res:
        st.error(res.json().get("detail", "Failed to generate quiz"))
    return None

def start_quiz(quiz_id: int):
    res = api("GET", f"/quizzes/{quiz_id}/start-quiz")
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to start quiz"))
    return None

def start_attempt(quiz_id: int):
    res = api("POST", "/start-attempt/", json={"quiz_id": quiz_id})
    if res and res.status_code == 200:
        return res.json().get("id")
    elif res:
        st.error(res.json().get("detail", "Failed to start attempt"))
    return False

def submit_answer(attempt_id: int, question_id: int, selected_option: str):
    res = api("POST", "/submit-answer/", json={"attempt_id": attempt_id, "question_id": question_id, "selected_option": selected_option})
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to submit answer"))
    return False

def submit_batch_answers(attempt_id: int, answers: list[dict]):
    """
    Submits multiple answers at once. 
    'answers' should be a list of dicts: [{"attempt_id": X, "question_id": Y, "selected_option": "Z"}, ...]
    """
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
    elif res:
        st.error(res.json().get("detail", "Failed to submit batch answers"))
    return None

def finish_attempt(attempt_id: int):
    res = api("POST", "/finish-attempt/", json={"attempt_id": attempt_id})
    if res and res.status_code == 200:
        return res.json()
    elif res:
        st.error(res.json().get("detail", "Failed to finish attempt"))
    return None
