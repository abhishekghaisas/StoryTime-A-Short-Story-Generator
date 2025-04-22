#!/bin/bash
set -e

# Download model files
python /home/site/wwwroot/download_model.py


# Download base model if not exists
if [ ! -d "/home/site/wwwroot/base_model" ]; then
  python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
    base_model='TinyLlama/TinyLlama-1.1B-Chat-v1.0'; \
    tokenizer = AutoTokenizer.from_pretrained(base_model); \
    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype='auto'); \
    model.save_pretrained('/home/site/wwwroot/base_model')"
fi

# Start the application
cd /home/site/wwwroot
export MODEL_PATH=/home/site/wwwroot/model
export TOKENIZERS_PARALLELISM=false

gunicorn -w 1 -k uvicorn.workers.UvicornWorker backend:app --bind=0.0.0.0:8000
