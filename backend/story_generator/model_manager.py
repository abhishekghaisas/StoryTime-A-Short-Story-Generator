"""
Model Manager module for story generation.

Handles loading, unloading and caching of models.
Implements efficient memory management for model usage.
"""

import torch
import os
import logging
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from backend.utils.memory_utils import clear_gpu_memory

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading and caching of AI models for story generation."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.models = {}          # Cache for models
        self.tokenizers = {}      # Cache for tokenizers
        self.default_model = None # Default model name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def load_model(self, model_path: str, force_reload: bool = False) -> tuple:
        """
        Load a model and tokenizer from the specified path.
        
        Args:
            model_path: Path to the model
            force_reload: Whether to force reload even if cached
        
        Returns:
            Tuple of (model, tokenizer)
        """
        # Check if model is already loaded and not forcing reload
        if model_path in self.models and not force_reload:
            logger.info(f"Using cached model from {model_path}")
            return self.models[model_path], self.tokenizers[model_path]
        
        # Set as default if no default exists
        if self.default_model is None:
            self.default_model = model_path
        
        # Clear memory before loading new model if using GPU
        if self.device.type == "cuda" and len(self.models) > 0:
            clear_gpu_memory()
        
        try:
            logger.info(f"Loading model from {model_path}...")
            
            # Determine appropriate dtype
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model with appropriate settings
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=dtype,
                device_map="auto"  # Automatically handles multi-GPU or CPU
            )
            
            # Cache the loaded model and tokenizer
            self.models[model_path] = model
            self.tokenizers[model_path] = tokenizer
            
            logger.info(f"Model loaded successfully from {model_path}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {str(e)}")
            raise
    
    def get_default_model(self) -> tuple:
        """
        Get the default model and tokenizer.
        
        Returns:
            Tuple of (model, tokenizer)
        """
        if self.default_model is None:
            raise ValueError("No default model has been loaded")
        
        return self.models[self.default_model], self.tokenizers[self.default_model]
    
    def unload_model(self, model_path: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_path: Path to the model to unload
            
        Returns:
            bool: Success or failure
        """
        if model_path not in self.models:
            logger.warning(f"Model {model_path} not loaded, cannot unload")
            return False
            
        try:
            # Remove from cache
            del self.models[model_path]
            del self.tokenizers[model_path]
            
            # Update default model if needed
            if self.default_model == model_path:
                self.default_model = next(iter(self.models.keys())) if self.models else None
            
            # Clear GPU memory
            if self.device.type == "cuda":
                clear_gpu_memory()
                
            logger.info(f"Model {model_path} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading model {model_path}: {str(e)}")
            return False
    
    def unload_all_models(self) -> bool:
        """
        Unload all models from memory.
        
        Returns:
            bool: Success or failure
        """
        try:
            # Clear model caches
            self.models.clear()
            self.tokenizers.clear()
            self.default_model = None
            
            # Clear GPU memory
            if self.device.type == "cuda":
                clear_gpu_memory()
                
            logger.info("All models unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading all models: {str(e)}")
            return False