import requests
import os

BASE_URL = "http://127.0.0.1:8000"

def run_seed():
    print("Starting LearningBuddy API Seeding Process...\n")

    # ==========================================
    # 1. AUTHENTICATION (Get the Wristband)
    # ==========================================
    user_payload = {"username": "Jia Jun", "password": "securepassword123"}
    
    print("Registering User...")
    reg_res = requests.post(f"{BASE_URL}/register/", json=user_payload)
    if reg_res.status_code == 400:
        print("   User already exists, proceeding to login...")
    elif reg_res.status_code != 200:
        print(f"Failed to register: {reg_res.text}")
        return

    print("Logging In...")
    login_res = requests.post(f"{BASE_URL}/login/", json=user_payload)
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
        
    token = login_res.json().get("access_token")
    # This header is your digital wristband! We attach it to all future requests.
    HEADERS = {"Authorization": f"Bearer {token}"}
    print("   Access Token Acquired!\n")


    # ==========================================
    # 2. CREATE SUBJECTS
    # ==========================================
    print("Creating Subjects...")
    subjects_to_create = ["CS335 - Software Engineering", "Machine Learning Foundations"]
    subject_ids = []

    for sub_name in subjects_to_create:
        res = requests.post(f"{BASE_URL}/subjects/", json={"name": sub_name}, headers=HEADERS)
        if res.status_code == 200:
            sub_id = res.json().get("id")
            subject_ids.append(sub_id)
            print(f"   Created Subject: {sub_name} (ID: {sub_id})")
        else:
            print(f"   Failed to create subject: {res.text}")


    # ==========================================
    # 3. CREATE TOPICS
    # ==========================================
    if len(subject_ids) < 2:
        print("Missing subjects, aborting topic creation.")
        return

    print("\nCreating Topics...")
    topics_data = [
        {"subject_id": subject_ids[0], "name": "Design Patterns & Architecture"},
        {"subject_id": subject_ids[0], "name": "API Security Models"},
        {"subject_id": subject_ids[1], "name": "Neural Networks"},
    ]
    topic_ids = []

    for t in topics_data:
        res = requests.post(f"{BASE_URL}/topics/", json=t, headers=HEADERS)
        if res.status_code == 200:
            top_id = res.json().get("id")
            topic_ids.append(top_id)
            print(f"   Created Topic: {t['name']} (ID: {top_id})")
        else:
            print(f"   Failed to create topic: {res.text}")


    # ==========================================
    # 4. UPLOAD MATERIAL (PDF Simulation)
    # ==========================================
    if not topic_ids:
        return
        
    print("\nUploading Study Material...")
    # Let's dynamically create a dummy PDF file to upload so the script is self-contained
    dummy_file_path = "dummy_notes.pdf"
    with open(dummy_file_path, "wb") as f:
        f.write(b"Mock PDF content for the AI to parse later.")

    # When sending files via requests, we don't use 'json=', we use 'files=' and 'data='
    with open(dummy_file_path, "rb") as f:
        files = {"file": (dummy_file_path, f, "application/pdf")}
        data = {"topic_id": topic_ids[0]}
        
        # Note: We don't send the "Content-Type: application/json" header for file uploads
        res = requests.post(f"{BASE_URL}/materials/upload", files=files, data=data, headers=HEADERS)
        
        if res.status_code == 200:
            print(f"   Material uploaded successfully to Topic ID {topic_ids[0]}!")
        else:
            print(f"   Failed to upload material: {res.text}")

    # Clean up the dummy file locally
    if os.path.exists(dummy_file_path):
        os.remove(dummy_file_path)

    # ==========================================
    # 5. TEST DASHBOARD FETCH
    # ==========================================
    print("\nFetching Final Dashboard...")
    dash_res = requests.get(f"{BASE_URL}/dashboard", headers=HEADERS)
    if dash_res.status_code == 200:
        print("   Dashboard fetched successfully! Data structure looks good.")
    else:
        print(f"Failed to fetch dashboard: {dash_res.text}")

    print("\nAPI Seeding Complete! The database is ready.")

if __name__ == "__main__":
    run_seed()