# LearningBuddy

An AI-powered study assistant that turns lecture content into active learning by generating questions, evaluating answers, identifying mistakes, and recommending personalized revision.

## Features

- Upload and process PDF, DOCX, and PPTX documents
- Generate quizzes from lecture materials
- AI-powered question evaluation and feedback
- Track learning progress and performance
- Interactive quiz interface
- Hallucination detection for AI responses
- Vector-based document search using embeddings

## Prerequisites

Before setting up the project, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd LearningBuddy-main1
   ```

2. **Set up environment variables:**

   Copy the provided `.env.example` file to `.env` and configure it with your own values:

   ```dotenv
   SECRET_KEY=<your-secure-secret-key>
   DATABASE_URL=<your-database-url>
   OLLAMA_URL=<your-ollama-url>
   OLLAMA_EMBEDDING_MODEL=<embedding-model>
   OLLAMA_QUIZ_MODEL=<quiz-model>
   OLLAMA_FEEDBACK_MODEL=<feedback-model>
   OLLAMA_TEMPERATURE=<temperature-value>
   OLLAMA_MAX_TOKENS=<max-tokens>
   OLLAMA_NUM_PARALLEL=<num-parallel>
   OLLAMA_MAX_LOADED_MODELS=<max-loaded-models>
   ```

   **Note:** Generate a secure `SECRET_KEY` for production use. Update all configuration values with your specific setup. Refer to `.env.example` for configuration details.

3. **Build and run the application:**

   ```bash
   docker-compose up --build
   ```

   This command will:
   - Build the frontend (Streamlit), backend (FastAPI), database (PostgreSQL with pgvector), and Ollama services
   - Start all services
   - Download the required Ollama models (this may take some time on first run)

4. **Initialize the database with test data:**

   Once all services are running and healthy, seed the database with test users and sample data:

   ```bash
   python backend/app/seed_api.py
   ```

   This will create test users and sample subjects/materials. Check the seed script for default credentials.

5. **Access the application:**

   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - Ollama API: http://localhost:11434

## Development Setup

If you prefer to run components locally without Docker:

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the frontend:
   ```bash
   streamlit run app.py
   ```

### Database

For local development, you can run PostgreSQL with pgvector locally or use the Docker container.

### Ollama

Install Ollama locally from https://ollama.ai and pull the required models:

```bash
ollama pull <embedding-model>
ollama pull <quiz-model>
```

## Usage

After seeding the database, you can log in with test users created by the seed script.

1. Access the frontend at the configured frontend URL
2. Upload lecture materials (PDF, DOCX, PPTX)
3. Generate quizzes from the uploaded content
4. Take quizzes and receive AI-powered feedback
5. Track your progress in the dashboard

## API Documentation

The backend provides a REST API. Access the interactive documentation at http://localhost:8000/docs when the backend is running.

## Project Structure

```
LearningBuddy-main1/
├── ai/                          # AI-related utilities
├── backend/                     # FastAPI backend
│   ├── app/                     # Application code
│   ├── Dockerfile               # Backend Docker configuration
│   └── requirements.txt         # Python dependencies
├── frontend/                    # Streamlit frontend
│   ├── pages/                   # Streamlit pages
│   ├── Dockerfile               # Frontend Docker configuration
│   └── requirements.txt         # Python dependencies
├── models/                      # Data models
├── scripts/                     # Utility scripts
├── tests/                       # Test files
├── docker-compose.yml           # Docker Compose configuration
├── docker-entrypoint.sh         # Docker entrypoint script
├── Dockerfile.ollama            # Ollama Docker configuration
├── .env                         # Environment variables
└── README.md                    # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Ollama models not downloading:**
   - Ensure you have sufficient disk space
   - Check internet connection
   - The initial download may take several minutes

2. **Database connection issues:**
   - Ensure the PostgreSQL container is healthy
   - Check the DATABASE_URL in .env

3. **Port conflicts:**
   - Ensure ports 8501, 8000, 5432, and 11434 are available
   - Modify docker-compose.yml if needed

### Logs

View logs for specific services:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
docker-compose logs ollama
```

## License

[Add license information here]



