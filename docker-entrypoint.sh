#!/bin/bash
set -e

# Start Ollama server in the background
echo "🚀 Starting Ollama server..."
/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready (max 60 seconds)
echo "⏳ Waiting for Ollama to become ready..."
for i in {1..60}; do
  if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is ready!"
    break
  fi
  echo "⏳ Waiting... ($i/60)"
  sleep 1
done

# Check and pull the embedding model if not already present
if ! curl -s http://localhost:11434/api/tags | grep -q "${OLLAMA_EMBEDDING_MODEL}"; then
  echo "📥 Pulling embedding model: ${OLLAMA_EMBEDDING_MODEL}..."
  ollama pull ${OLLAMA_EMBEDDING_MODEL} || echo "⚠️ Failed to pull ${OLLAMA_EMBEDDING_MODEL}"
else
  echo "✅ Embedding model ${OLLAMA_EMBEDDING_MODEL} already exists"
fi

# Check and pull the quiz model if not already present
if ! curl -s http://localhost:11434/api/tags | grep -q "${OLLAMA_QUIZ_MODEL}"; then
  echo "📥 Pulling quiz model: ${OLLAMA_QUIZ_MODEL}..."
  ollama pull ${OLLAMA_QUIZ_MODEL} || echo "⚠️ Failed to pull ${OLLAMA_QUIZ_MODEL}"
else
  echo "✅ Quiz model ${OLLAMA_QUIZ_MODEL} already exists"
fi

# Check and pull the feedback model if different from quiz model and not already present
if [ "${OLLAMA_FEEDBACK_MODEL}" != "${OLLAMA_QUIZ_MODEL}" ]; then
  if ! curl -s http://localhost:11434/api/tags | grep -q "${OLLAMA_FEEDBACK_MODEL}"; then
    echo "📥 Pulling feedback model: ${OLLAMA_FEEDBACK_MODEL}..."
    ollama pull ${OLLAMA_FEEDBACK_MODEL} || echo "⚠️ Failed to pull ${OLLAMA_FEEDBACK_MODEL}"
  else
    echo "✅ Feedback model ${OLLAMA_FEEDBACK_MODEL} already exists"
  fi
fi

# Keep Ollama running in foreground
echo "✅ Models ready. Ollama is running..."
wait $OLLAMA_PID
