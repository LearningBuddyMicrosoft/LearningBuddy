def seed_data():
    from sqlmodel import Session, SQLModel
    from .database import engine
    from .models import User, Subject, Topic, Material, Question

    print("Resetting database...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:

        # --- USERS ---
        users = [
            User(username="Jia Jun"),
            User(username="Alice"),
            User(username="Bob"),
        ]
        session.add_all(users)
        session.commit()

        # --- SUBJECTS ---
        subjects = [
            Subject(name="Java Programming", user_id=users[0].id),
            Subject(name="Unix Architecture", user_id=users[0].id),
            Subject(name="Python & FastAPI", user_id=users[1].id),
            Subject(name="Data Structures", user_id=users[2].id),
        ]
        session.add_all(subjects)
        session.commit()

        # --- TOPICS ---
        topics = [
            Topic(name="Design Patterns", subject_id=subjects[0].id),
            Topic(name="Memory Management", subject_id=subjects[1].id),
            Topic(name="APIs", subject_id=subjects[2].id),
            Topic(name="Trees", subject_id=subjects[3].id),
            Topic(name="Sorting", subject_id=subjects[3].id),
        ]
        session.add_all(topics)
        session.commit()

        # --- MATERIALS ---
        materials = [
            Material(name="Design Patterns PDF", file_path="/files/design_patterns.pdf", topic_id=topics[0].id),
            Material(name="Unix Memory Notes", file_path="/files/unix_memory.pdf", topic_id=topics[1].id),
            Material(name="FastAPI Guide", file_path="/files/fastapi.pdf", topic_id=topics[2].id),
        ]
        session.add_all(materials)

        # --- QUESTIONS ---
        questions = [
            # Design Patterns
            Question(
                topic_id=topics[0].id,
                difficulty=2,
                question_type="MCQ",
                question_text="Which pattern allows incompatible interfaces to work together?",
                options=["Builder", "Decorator", "Adapter", "Singleton"],
                correct_answer="Adapter"
            ),
            Question(
                topic_id=topics[0].id,
                difficulty=3,
                question_type="MCQ",
                question_text="Which pattern wraps objects to add behavior?",
                options=["Decorator", "Factory", "Observer", "Adapter"],
                correct_answer="Decorator"
            ),

            # Unix
            Question(
                topic_id=topics[1].id,
                difficulty=1,
                question_type="MCQ",
                question_text="What does RAM stand for?",
                options=["Random Access Memory", "Read Access Memory", "Run Access Memory", "None"],
                correct_answer="Random Access Memory"
            ),

            # FastAPI
            Question(
                topic_id=topics[2].id,
                difficulty=2,
                question_type="MCQ",
                question_text="Which keyword defines a route in FastAPI?",
                options=["@route", "@app.get", "@api", "@endpoint"],
                correct_answer="@app.get"
            ),

            # Trees
            Question(
                topic_id=topics[3].id,
                difficulty=2,
                question_type="MCQ",
                question_text="What is the root of a tree?",
                options=["Top node", "Leaf node", "Middle node", "None"],
                correct_answer="Top node"
            ),

            # Sorting
            Question(
                topic_id=topics[4].id,
                difficulty=3,
                question_type="MCQ",
                question_text="Which sorting algorithm is O(n log n)?",
                options=["Bubble Sort", "Merge Sort", "Insertion Sort", "Selection Sort"],
                correct_answer="Merge Sort"
            ),
        ]

        session.add_all(questions)
        session.commit()

        print("Database seeded with rich dataset!")

if __name__ == "__main__":
    seed_data()