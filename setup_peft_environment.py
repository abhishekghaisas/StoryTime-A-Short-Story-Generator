#!/usr/bin/env python3
"""
Setup script for TinyLlama LoRA adapter model CPU inference

This script sets up the environment for running TinyLlama models with LoRA adapters on CPU.
It installs necessary dependencies and checks the system configuration.
"""

import os
import sys
import subprocess
import logging
import json
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required dependencies for PEFT/LoRA inference"""
    packages = [
        "transformers>=4.31.0",
        "accelerate",
        "peft",         # Required for LoRA adapter loading
        "bitsandbytes",  # For 8-bit quantization
        "safetensors",   # For loading safetensors adapter weights
        "psutil"         # For system monitoring
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

def verify_adapter_model(model_path):
    """Verify that the adapter model is properly formatted"""
    adapter_config_path = os.path.join(model_path, "adapter_config.json")
    adapter_model_path_safetensors = os.path.join(model_path, "adapter_model.safetensors")
    adapter_model_path_bin = os.path.join(model_path, "adapter_model.bin")
    
    issues = []
    
    # Check adapter config
    if not os.path.exists(adapter_config_path):
        issues.append(f"Missing adapter_config.json in {model_path}")
    else:
        logger.info("Found adapter_config.json ✓")
        
        # Read and validate adapter config
        try:
            with open(adapter_config_path, "r") as f:
                adapter_config = json.load(f)
            
            # Check essential fields
            if "base_model_name_or_path" not in adapter_config:
                issues.append("adapter_config.json is missing base_model_name_or_path field")
            else:
                logger.info(f"Base model: {adapter_config['base_model_name_or_path']} ✓")
                
            if "peft_type" not in adapter_config or adapter_config["peft_type"] != "LORA":
                issues.append("adapter_config.json does not specify LORA as peft_type")
            else:
                logger.info("PEFT type is LORA ✓")
        except Exception as e:
            issues.append(f"Error reading adapter_config.json: {str(e)}")
    
    # Check adapter model weights
    if os.path.exists(adapter_model_path_safetensors):
        logger.info("Found adapter_model.safetensors ✓")
    elif os.path.exists(adapter_model_path_bin):
        logger.info("Found adapter_model.bin ✓")
    else:
        issues.append(f"Missing adapter weights (adapter_model.safetensors or adapter_model.bin) in {model_path}")
    
    # Check tokenizer files
    tokenizer_files = [
        "tokenizer_config.json",
        "special_tokens_map.json"
    ]
    
    for file in tokenizer_files:
        if os.path.exists(os.path.join(model_path, file)):
            logger.info(f"Found {file} ✓")
        else:
            issues.append(f"Missing {file} in {model_path}")
    
    # Report validation results
    if issues:
        logger.warning("Issues found with adapter model:")
        for issue in issues:
            logger.warning(f"- {issue}")
        return False
    else:
        logger.info("Adapter model verification successful! ✓")
        return True

def create_environment_file(model_path):
    """Create environment file with model path and optimizations"""
    env_content = f"""# Environment variables for TinyLlama LoRA adapter model
MODEL_PATH="{model_path}"

# Performance optimizations
TOKENIZERS_PARALLELISM=false
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    logger.info("Created .env file with model path and optimizations")

def create_test_script(model_path):
    """Create a test script to verify model loading"""
    test_script = """#!/usr/bin/env python3
\"\"\"
Test script for TinyLlama LoRA adapter model

This script verifies that the model can be loaded correctly.
\"\"\"

import os
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    \"\"\"Test loading the LoRA adapter model\"\"\"
    model_path = os.environ.get("MODEL_PATH", "{0}")
    logger.info(f"Testing model loading from: {{model_path}}")
    
    # Check if this is a PEFT/LoRA adapter model
    is_peft_model = os.path.exists(os.path.join(model_path, "adapter_config.json"))
    
    if is_peft_model:
        logger.info("Detected PEFT/LoRA adapter model")
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load base model from adapter config
        import json
        with open(os.path.join(model_path, "adapter_config.json"), "r") as f:
            adapter_config = json.load(f)
        
        base_model_name = adapter_config["base_model_name_or_path"]
        logger.info(f"Loading base model: {{base_model_name}}")
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name, 
            torch_dtype=torch.float32, 
            low_cpu_mem_usage=True
        )
        
        # Load PEFT adapter
        from peft import PeftModel
        logger.info("Loading PEFT adapter...")
        model = PeftModel.from_pretrained(base_model, model_path)
        
        # Test generation
        prompt = "Once upon a time,"
        logger.info(f"Testing generation with prompt: '{{prompt}}'")
        
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(inputs.input_ids, max_new_tokens=20)
        generated_text = tokenizer.decode(outputs[0])
        
        logger.info(f"Generated text: '{{generated_text}}'")
        logger.info("Test completed successfully!")
    else:
        logger.error(f"Not a PEFT/LoRA adapter model: {{model_path}}")

if __name__ == "__main__":
    main()
""".format(model_path)
    
    with open("test_lora_model.py", "w") as f:
        f.write(test_script)
    
    # Make executable
    try:
        os.chmod("test_lora_model.py", 0o755)
    except Exception as e:
        logger.warning(f"Could not make script executable: {e}")
    
    logger.info("Created test script: test_lora_model.py")

def find_adapter_model_file(base_dir):
    """Search for adapter_model.safetensors or adapter_model.bin in the directory tree"""
    logger.info(f"Searching for adapter model file in {base_dir} and parent directories...")
    
    # Check current directory
    adapter_files = [
        os.path.join(base_dir, "adapter_model.safetensors"),
        os.path.join(base_dir, "adapter_model.bin")
    ]
    
    for file_path in adapter_files:
        if os.path.exists(file_path):
            logger.info(f"Found adapter file: {file_path}")
            return file_path
    
    # Check parent directory
    parent_dir = os.path.dirname(base_dir)
    if parent_dir != base_dir:  # Avoid infinite recursion at root
        adapter_files = [
            os.path.join(parent_dir, "adapter_model.safetensors"),
            os.path.join(parent_dir, "adapter_model.bin")
        ]
        
        for file_path in adapter_files:
            if os.path.exists(file_path):
                logger.info(f"Found adapter file in parent directory: {file_path}")
                return file_path
    
    # Try wider search
    logger.info("Performing wider search for adapter files...")
    for root, dirs, files in os.walk(os.path.dirname(base_dir)):
        for file in files:
            if file in ["adapter_model.safetensors", "adapter_model.bin"]:
                file_path = os.path.join(root, file)
                logger.info(f"Found adapter file: {file_path}")
                return file_path
    
    logger.warning("No adapter model file found")
    return None

def fix_model_structure(model_path):
    """Attempt to fix common model structure issues"""
    
    # Search for adapter model file
    adapter_file = find_adapter_model_file(model_path)
    
    if adapter_file:
        # Copy to model directory if not already there
        target_path = os.path.join(model_path, os.path.basename(adapter_file))
        if os.path.abspath(adapter_file) != os.path.abspath(target_path):
            logger.info(f"Copying {adapter_file} to {target_path}...")
            
            import shutil
            try:
                shutil.copy(adapter_file, target_path)
                logger.info(f"Copied adapter file to model directory")
                return True
            except Exception as e:
                logger.error(f"Error copying adapter file: {e}")
    
    return False

def main():
    """Main function"""
    logger.info("Setting up environment for TinyLlama LoRA adapter model")
    
    # Get model path
    model_path = os.environ.get("MODEL_PATH", None)
    if not model_path:
        default_path = "/Users/abhishek/Desktop/Projects/StoryTime-A-Short-Story-Generator/tinyllama_1500stories_model"
        model_path = input(f"Enter path to your LoRA adapter model [default: {default_path}]: ").strip()
        if not model_path:
            model_path = default_path
    
    # Verify model path exists
    if not os.path.exists(model_path):
        logger.error(f"Model path does not exist: {model_path}")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Verify adapter model structure
    model_valid = verify_adapter_model(model_path)
    
    # Try to fix model structure if needed
    if not model_valid:
        logger.info("Attempting to fix model structure...")
        fixed = fix_model_structure(model_path)
        if fixed:
            logger.info("Model structure fixed! Reverifying...")
            model_valid = verify_adapter_model(model_path)
    
    if model_valid:
        logger.info("Model structure is valid!")
    else:
        logger.warning("Model structure issues remain. Loading may still fail.")
        continue_anyway = input("Continue setup anyway? (y/n): ").lower() == 'y'
        if not continue_anyway:
            logger.error("Setup aborted")
            sys.exit(1)
    
    # Create environment file
    create_environment_file(model_path)
    
    # Create test script
    create_test_script(model_path)
    
    logger.info("Setup completed!")
    logger.info("Next steps:")
    logger.info("1. Run test script to verify model loading: python test_lora_model.py")
    logger.info("2. Start your server with the model: source .env && python -m uvicorn backend:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()