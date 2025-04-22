#!/bin/bash
set -e

# Download model files
python /home/site/wwwroot/model_setup.py


# Start the application
cd /home/site/wwwroot
export MODEL_PATH=/home/site/wwwroot/model
export TOKENIZERS_PARALLELISM=false

gunicorn --bind=0.0.0.0 --timeout 600 --workers 1 --threads 8 -k uvicorn.workers.UvicornWorker backend:app
