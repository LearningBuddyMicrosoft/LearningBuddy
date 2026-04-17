import os

from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True) #shows the SQL in terminal

# 3. INITIALIZE THE DATABASE
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    # Run this once to create the file and tables
    create_db_and_tables()
    print("Database and tables created successfully!")

def get_session():
    with Session(engine) as session:
        yield session