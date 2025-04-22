# download_model.py
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

def download_model_files():
    # Configuration
    storage_account_name = "napnap"  # Replace with your storage account name
    container_name = "model-files"                # Replace with your container name
    model_dir = os.path.join(os.getcwd(), "model")
    
    # Create model directory
    os.makedirs(model_dir, exist_ok=True)
    
    # Get credential using Managed Identity
    credential = DefaultAzureCredential()
    
    # Create blob service client
    account_url = f"https://{storage_account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
    
    # Get container client
    container_client = blob_service_client.get_container_client(container_name)
    
    # Model files to download
    files_to_download = [
        "adapter_config.json",
        "adapter_model.safetensors",
        "tokenizer_config.json",
        "special_tokens_map.json"
    ]
    
    # Download each file
    for file_name in files_to_download:
        print(f"Downloading {file_name}...")
        blob_client = container_client.get_blob_client(file_name)
        
        download_path = os.path.join(model_dir, file_name)
        with open(download_path, "wb") as file:
            data = blob_client.download_blob()
            file.write(data.readall())
        
        print(f"Downloaded {file_name} to {download_path}")

if __name__ == "__main__":
    download_model_files()
