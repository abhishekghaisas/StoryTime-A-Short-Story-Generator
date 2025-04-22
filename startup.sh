#!/bin/bash
set -e

# Create model directory
mkdir -p /home/site/wwwroot/model


# Download model files from Azure Storage
echo "Downloading model files..."
curl -o /home/site/wwwroot/model/adapter_config.json "https://storygeneratorfiles.blob.core.windows.net/model-files/adapter_config.json"
curl -o /home/site/wwwroot/model/adapter_model.safetensors "https://storygeneratorfiles.blob.core.windows.net/model-files/adapter_model.safetensors"
curl -o /home/site/wwwroot/model/tokenizer_config.json "https://storygeneratorfiles.blob.core.windows.net/model-files/tokenizer_config.json"
curl -o /home/site/wwwroot/model/special_tokens_map.json "https://storygeneratorfiles.blob.core.windows.net/model-files/special_tokens_map.json"

# Download model files
python /home/site/wwwroot/model_setup.py



# Start the application
cd /home/site/wwwroot
export MODEL_PATH=/home/site/wwwroot/model
export TOKENIZERS_PARALLELISM=false

gunicorn --bind=0.0.0.0 --timeout 600 --workers 1 --threads 8 -k uvicorn.workers.UvicornWorker backend:app
