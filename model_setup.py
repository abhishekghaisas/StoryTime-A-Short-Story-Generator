# model_setup.py
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

def download_model_files():
    storage_account_name = "storygeneratorfiles"
    container_name = "model-files"
    model_dir = "/home/site/wwwroot/model"
    
    # Create model directory if it doesn't exist
    os.makedirs(model_dir, exist_ok=True)
    
    # Use managed identity
    credential = DefaultAzureCredential()
    
    # Initialize blob service client
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=credential
    )
    
    # Get container client
    container_client = blob_service_client.get_container_client(container_name)
    
    # List of model files to download
    model_files = [
        "adapter_config.json",
        "adapter_model.safetensors",
        "tokenizer_config.json",
        "special_tokens_map.json"
    ]
    
    # Download each file
    for file_name in model_files:
        print(f"Downloading {file_name}...")
        blob_client = container_client.get_blob_client(file_name)
        with open(os.path.join(model_dir, file_name), "wb") as file:
            file.write(blob_client.download_blob().readall())
    
    print("Model files downloaded successfully")

if __name__ == "__main__":
    download_model_files()
