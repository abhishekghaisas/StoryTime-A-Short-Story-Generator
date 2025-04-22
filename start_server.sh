#!/bin/bash
# Startup script for TinyLlama CPU inference server

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Set model path
export MODEL_PATH="/Users/abhishek/Desktop/Projects/StoryTime-A-Short-Story-Generator/tinyllama_1500stories_model"

# Start server with optimized settings
python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --workers 1

# If using Windows, use this command instead:
# python -m uvicorn backend:app --host 0.0.0.0 --port 8000
