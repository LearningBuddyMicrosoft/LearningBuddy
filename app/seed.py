from sqlmodel import Session, SQLModel
from database import engine 
# ADDED: Don't forget to import Quiz!
from models import User, Subject, Topic, Material, Question, Quiz


#run to create local test data
def seed_data():
    print("Clearing old database tables...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    print("Seeding personalized test data...")
    with Session(engine) as session:
        
        # 1. Create Test Users
        user1 = User(username="Jia Jun")
        user2 = User(username="Alice")
        session.add_all([user1, user2])
        session.commit() # Commit right away so they get their IDs!

        # 2. Create the Curriculum (Now tied to specific users!)
        # user1 gets Java and Unix subjects
        subject_java = Subject(name="Java Programming", user_id=user1.id)
        subject_unix = Subject(name="Unix Architecture", user_id=user1.id)
        
        # user2 gets a Python subject
        subject_python = Subject(name="Python & FastAPI", user_id=user2.id)
        
        session.add_all([subject_java, subject_unix, subject_python])
        session.commit() # Commit so Subjects get IDs!

        # 3. Add Topics to User 1's Java Subject
        topic_patterns = Topic(name="Design Patterns", subject_id=subject_java.id)
        session.add(topic_patterns)
        session.commit() 

        # 4. Add some Mock Lecture Materials
        material_adapter = Material(
            name="Structural Patterns Slides", 
            file_path="/materials/java/structural_patterns.pdf", 
            topic_id=topic_patterns.id
        )
        session.add(material_adapter)

        # 5. Add the Question Bank
        q1 = Question(
            topic_id=topic_patterns.id,
            difficulty= 2,
            question_type="MCQ",
            question_text="Which pattern allows incompatible interfaces to work together?",
            options=["Builder", "Decorator", "Adapter", "Singleton"],
            correct_answer="Adapter"
        )
        q2 = Question(
            topic_id=topic_patterns.id,
            difficulty= 3,
            question_type="MCQ",
            question_text="Which pattern lets you attach new behaviors to objects by placing them inside wrapper objects?",
            options=["Decorator", "Builder", "Factory", "Adapter"],
            correct_answer="Decorator"
        )
        session.add_all([q1, q2])
        session.commit() # Commit so the questions get their IDs!

        # 6. Build the Test Paper (The Quiz)
        print("Building Quiz...")
        mock_quiz = Quiz(
            user_id=user1.id,
            name="Design Patterns Midterm Review",
            open_ended=False,
            length=2,
            highscore=0
        )
        
        # The SQLModel Magic: Link the Topic and the Questions directly to the Quiz
        mock_quiz.topics.append(topic_patterns)
        mock_quiz.questions.extend([q1, q2]) # .extend() is like append, but for a list!
        
        session.add(mock_quiz)

        # Save everything to the database
        session.commit()
        print("Database successfully seeded! User-specific subjects and quizzes created.")

if __name__ == "__main__":
    seed_data()
    print("Seeding completed successfully.")