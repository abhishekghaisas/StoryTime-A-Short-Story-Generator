#!/bin/bash
set -e

# Create log directory
mkdir -p /home/site/wwwroot/logs

# Log startup progress
echo "$(date): Starting application setup..." > /home/site/wwwroot/logs/startup.log

# Create model directory with error handling
mkdir -p /home/site/wwwroot/model
if [ ! -d "/home/site/wwwroot/model" ]; then
    echo "$(date): Failed to create model directory" >> /home/site/wwwroot/logs/startup.log
    exit 1
fi
echo "$(date): Model directory created" >> /home/site/wwwroot/logs/startup.log

# Verify we can write to model directory
touch /home/site/wwwroot/model/test.txt
if [ ! -f "/home/site/wwwroot/model/test.txt" ]; then
    echo "$(date): Cannot write to model directory" >> /home/site/wwwroot/logs/startup.log
    exit 1
fi
rm /home/site/wwwroot/model/test.txt
echo "$(date): Write access confirmed" >> /home/site/wwwroot/logs/startup.log

# List container files to verify access
echo "$(date): Listing files in container:" >> /home/site/wwwroot/logs/startup.log
python -c "
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

try:
    storage_account_name = 'napnap'
    container_name = 'model-files'
    
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(
        account_url=f'https://{storage_account_name}.blob.core.windows.net',
        credential=credential
    )
    
    container_client = blob_service_client.get_container_client(container_name)
    
    print('Files in container:')
    for blob in container_client.list_blobs():
        print(f' - {blob.name} ({blob.size} bytes)')
    
except Exception as e:
    print(f'Error accessing storage: {str(e)}')
" >> /home/site/wwwroot/logs/startup.log

# Create a minimal test app to verify basic functionality
echo "$(date): Creating test app..." >> /home/site/wwwroot/logs/startup.log
cat > /home/site/wwwroot/test_app.py << 'EOL'
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "OK", "message": "Test app running"}

@app.get("/check-model")
async def check_model():
    model_path = os.environ.get("MODEL_PATH", "/home/site/wwwroot/model")
    if not os.path.exists(model_path):
        return {"status": "ERROR", "message": f"Model path not found: {model_path}"}
    
    files = os.listdir(model_path)
    return {
        "status": "OK", 
        "model_path": model_path,
        "files": files
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOL

# Try running this test app first to diagnose issues
echo "$(date): Starting test app to diagnose issues..." >> /home/site/wwwroot/logs/startup.log
cd /home/site/wwwroot
export MODEL_PATH=/home/site/wwwroot/model
export TOKENIZERS_PARALLELISM=false

python test_app.py
