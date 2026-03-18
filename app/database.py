from sqlmodel import SQLModel, create_engine

sqlite_url = "sqlite:///learning_buddy.db"
engine = create_engine(sqlite_url, echo=True) #shows the SQL in terminal

# 3. INITIALIZE THE DATABASE
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    # Run this once to create the file and tables
    create_db_and_tables()
    print("Database and tables created successfully!")