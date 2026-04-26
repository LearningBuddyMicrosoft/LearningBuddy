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
if ! curl -s http://localhost:11434/api/tags | grep -q "nomic-embed-text"; then
  echo "📥 Pulling embedding model: nomic-embed-text..."
  ollama pull nomic-embed-text || echo "⚠️ Failed to pull nomic-embed-text"
else
  echo "✅ Embedding model nomic-embed-text already exists"
fi

# Check and pull the LLM model if not already present
if ! curl -s http://localhost:11434/api/tags | grep -q "qwen2.5:1.5b-instruct"; then
  echo "📥 Pulling LLM model: qwen2.5:1.5b-instruct..."
  ollama pull qwen2.5:1.5b-instruct || echo "⚠️ Failed to pull qwen2.5:1.5b-instruct"
else
  echo "✅ LLM model qwen2.5:1.5b-instruct already exists"
fi

# Keep Ollama running in foreground
echo "✅ Models ready. Ollama is running..."
wait $OLLAMA_PID
