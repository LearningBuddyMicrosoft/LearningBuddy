# Use a lightweight Python image
FROM python:3.11-slim
# Set the working directory inside the container
WORKDIR /app
ENV PYTHONPATH="/app"
# Copy the requirements file first
COPY backend/requirements.txt ./requirements.txt
# Install FastAPI, Uvicorn, SQLModel, etc.
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt
# Copy the backend application code
COPY backend/ .
# Expose FastAPI's default port
EXPOSE 8000
# The command to start the server (we override this in docker-compose with --reload for dev mode)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]