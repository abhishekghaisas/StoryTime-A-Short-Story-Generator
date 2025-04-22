"""
Memory utilities for optimizing model resource usage.

Provides tools for memory management when using large models.
"""

import gc
import torch
import logging
import psutil
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_memory_usage() -> Dict[str, Any]:
    """
    Get current memory usage statistics.
    
    Returns:
        dict: Memory usage statistics
    """
    memory_stats = {
        "ram_used_gb": psutil.virtual_memory().used / (1024 ** 3),
        "ram_available_gb": psutil.virtual_memory().available / (1024 ** 3),
        "ram_percent": psutil.virtual_memory().percent
    }
    
    # Add GPU stats if available
    if torch.cuda.is_available():
        memory_stats.update({
            "gpu_allocated_gb": torch.cuda.memory_allocated() / (1024 ** 3),
            "gpu_reserved_gb": torch.cuda.memory_reserved() / (1024 ** 3),
            "gpu_max_memory_gb": torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        })
    
    return memory_stats

def log_memory_usage(level: str = "info"):
    """
    Log current memory usage statistics.
    
    Args:
        level: Logging level ('debug', 'info', 'warning')
    """
    mem_stats = get_memory_usage()
    
    # Format the message
    message = f"Memory usage - RAM: {mem_stats['ram_used_gb']:.2f}GB ({mem_stats['ram_percent']}%)"
    
    if torch.cuda.is_available():
        message += f", GPU: {mem_stats['gpu_allocated_gb']:.2f}GB allocated / {mem_stats['gpu_max_memory_gb']:.2f}GB total"
        
    # Log at appropriate level
    if level.lower() == "debug":
        logger.debug(message)
    elif level.lower() == "warning":
        logger.warning(message)
    else:
        logger.info(message)

def clear_gpu_memory():
    """
    Clear GPU memory cache to free up resources.
    """
    if torch.cuda.is_available():
        # Log before clearing
        before_stats = get_memory_usage()
        logger.info(f"GPU memory before clearing: {before_stats['gpu_allocated_gb']:.2f}GB allocated")
        
        # Clear CUDA cache
        torch.cuda.empty_cache()
        
        # Run garbage collection
        gc.collect()
        
        # Log after clearing
        after_stats = get_memory_usage()
        logger.info(f"GPU memory after clearing: {after_stats['gpu_allocated_gb']:.2f}GB allocated")
        
        freed_memory = before_stats['gpu_allocated_gb'] - after_stats['gpu_allocated_gb']
        logger.info(f"Freed {freed_memory:.2f}GB of GPU memory")
    else:
        logger.debug("No GPU available, skipping GPU memory clearing")

def optimize_for_inference(model: torch.nn.Module, device: torch.device = None):
    """
    Optimize a model for inference to reduce memory usage.
    
    Args:
        model: The model to optimize
        device: Target device (default: current device)
    
    Returns:
        The optimized model
    """
    if device is None:
        device = next(model.parameters()).device
    
    # Ensure eval mode
    model.eval()
    
    # Disable gradient computation
    for param in model.parameters():
        param.requires_grad = False
    
    # Try torch.compile if available (PyTorch 2.0+)
    try:
        if hasattr(torch, 'compile') and device.type == 'cuda':
            logger.info("Using torch.compile for inference optimization")
            model = torch.compile(model)
    except Exception as e:
        logger.warning(f"Could not use torch.compile: {str(e)}")
    
    return model

def check_memory_requirements(model_path: str, batch_size: int = 1) -> bool:
    """
    Check if there's enough memory to load and run a model.
    
    Args:
        model_path: Path to the model
        batch_size: Batch size for inference
    
    Returns:
        bool: Whether there's enough memory
    """
    # Estimate memory requirements based on model size and batch size
    model_size_gb = 0
    
    # If it's a directory, sum up file sizes
    if os.path.isdir(model_path):
        for dirpath, dirnames, filenames in os.walk(model_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                model_size_gb += os.path.getsize(file_path) / (1024 ** 3)
    
    # Add margin for runtime overhead (activation memory)
    estimated_memory_gb = model_size_gb * 1.5 * batch_size
    
    # Get available memory
    mem_stats = get_memory_usage()
    available_memory_gb = 0
    
    if torch.cuda.is_available():
        # For GPU, consider remaining GPU memory
        available_memory_gb = mem_stats['gpu_max_memory_gb'] - mem_stats['gpu_allocated_gb']
    else:
        # For CPU, consider system RAM
        available_memory_gb = mem_stats['ram_available_gb']
    
    # Determine if enough memory is available
    has_enough_memory = available_memory_gb >= estimated_memory_gb
    
    # Log the result
    if has_enough_memory:
        logger.info(f"Memory check passed: {available_memory_gb:.2f}GB available, {estimated_memory_gb:.2f}GB required")
    else:
        logger.warning(f"Memory check failed: {available_memory_gb:.2f}GB available, {estimated_memory_gb:.2f}GB required")
    
    return has_enough_memory