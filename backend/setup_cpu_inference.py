"""
Setup script for optimizing TinyLlama CPU inference

This script installs required dependencies and sets up the environment
for optimal CPU inference with the TinyLlama model.
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required dependencies for CPU inference"""
    packages = [
        "transformers>=4.31.0",
        "accelerate",
        "bitsandbytes",   # For model quantization
        "safetensors",    # For loading model weights
        "py-cpuinfo",     # For CPU capability detection
        "psutil"          # For system resource monitoring
    ]
    
    logger.info("Installing required dependencies...")
    
    for package in packages:
        try:
            logger.info(f"Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to install {package}: {e}")
    
    logger.info("Dependencies installed successfully")

def set_environment_variables():
    """Set environment variables for better performance"""
    # Variables to set
    env_vars = {
        "TOKENIZERS_PARALLELISM": "false",  # Disable parallelism in tokenizers
        "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:128"  # Memory allocation config
    }
    
    logger.info("Setting environment variables...")
    
    # Create .env file
    with open(".env", "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
            os.environ[key] = value
    
    logger.info("Environment variables set and saved to .env file")
    logger.info("Remember to load these variables before running the server")

def check_cpu_compatibility():
    """Check CPU compatibility for TinyLlama inference"""
    logger.info("Checking CPU compatibility...")
    
    try:
        import cpuinfo
        import psutil
        
        # Get CPU info
        info = cpuinfo.get_cpu_info()
        cpu_name = info.get('brand_raw', 'Unknown CPU')
        
        # Check for AVX2 support
        has_avx2 = 'avx2' in info.get('flags', [])
        
        # Check number of cores
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        
        # Check available RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        # Print results
        logger.info(f"CPU: {cpu_name}")
        logger.info(f"CPU cores: {cpu_cores} physical, {cpu_threads} logical")
        logger.info(f"RAM: {ram_gb:.2f} GB")
        logger.info(f"AVX2 support: {'Yes' if has_avx2 else 'No'}")
        
        # Check compatibility
        if not has_avx2:
            logger.warning("AVX2 not supported - TinyLlama inference may be very slow")
        
        if cpu_cores < 4:
            logger.warning("Low core count - inference may be slow")
        
        if ram_gb < 8:
            logger.warning("Less than 8GB RAM - may encounter memory issues")
        
        return has_avx2, cpu_cores, ram_gb
    
    except ImportError:
        logger.warning("Could not check CPU compatibility - missing dependencies")
        return None, None, None

def create_startup_script(model_path):
    """Create a startup script with optimized settings"""
    script_content = f"""#!/bin/bash
# Startup script for TinyLlama CPU inference server

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Set model path
export MODEL_PATH="{model_path}"

# Start server with optimized settings
python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --workers 1

# If using Windows, use this command instead:
# python -m uvicorn backend:app --host 0.0.0.0 --port 8000
"""
    
    # Write script to file
    script_path = "start_server.sh"
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make executable
    try:
        os.chmod(script_path, 0o755)
    except Exception as e:
        logger.warning(f"Could not make script executable: {e}")
    
    logger.info(f"Created startup script: {script_path}")
    
    # Create Windows batch file version
    batch_content = f"""@echo off
REM Startup script for TinyLlama CPU inference server

REM Set model path
set MODEL_PATH={model_path}

REM Set environment variables
set TOKENIZERS_PARALLELISM=false
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

REM Start server
python -m uvicorn backend:app --host 0.0.0.0 --port 8000
"""
    
    batch_path = "start_server.bat"
    with open(batch_path, "w") as f:
        f.write(batch_content)
    
    logger.info(f"Created Windows batch file: {batch_path}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Setup TinyLlama for CPU inference")
    parser.add_argument("--model_path", type=str, default=None, help="Path to TinyLlama model")
    parser.add_argument("--skip_deps", action="store_true", help="Skip dependency installation")
    args = parser.parse_args()
    
    logger.info("Setting up TinyLlama for CPU inference...")
    
    # Install dependencies
    if not args.skip_deps:
        install_dependencies()
    else:
        logger.info("Skipping dependency installation")
    
    # Check CPU compatibility
    check_cpu_compatibility()
    
    # Set environment variables
    set_environment_variables()
    
    # Get model path
    model_path = args.model_path
    if not model_path:
        default_path = "/Users/abhishek/Desktop/Projects/StoryTime-A-Short-Story-Generator/tinyllama_1500stories_model"
        model_path = input(f"Enter the path to your TinyLlama model [default: {default_path}]: ").strip()
        if not model_path:
            model_path = default_path
    
    # Validate model path
    if not os.path.exists(model_path):
        logger.warning(f"Model path does not exist: {model_path}")
        create_anyway = input("Create startup scripts anyway? (y/n): ").lower() == 'y'
        if not create_anyway:
            logger.error("Setup aborted")
            return
    
    # Create startup scripts
    create_startup_script(model_path)
    
    logger.info("Setup completed successfully!")
    logger.info("To start the server, run: ./start_server.sh (Linux/macOS) or start_server.bat (Windows)")

if __name__ == "__main__":
    main()