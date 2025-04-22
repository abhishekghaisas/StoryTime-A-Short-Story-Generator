"""
Text Generator module for story generation.

Handles the actual text generation using loaded models.
"""

import torch
import logging
from typing import Dict, Any, Optional
from transformers import PreTrainedModel, PreTrainedTokenizer

logger = logging.getLogger(__name__)

class TextGenerator:
    """Handles text generation using transformer models."""
    
    def __init__(self, model: Optional[PreTrainedModel] = None, 
                tokenizer: Optional[PreTrainedTokenizer] = None):
        """
        Initialize the text generator.
        
        Args:
            model: Optional pre-loaded model
            tokenizer: Optional pre-loaded tokenizer
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def set_model_and_tokenizer(self, model: PreTrainedModel, 
                              tokenizer: PreTrainedTokenizer) -> None:
        """
        Set the model and tokenizer for generation.
        
        Args:
            model: The pre-trained model
            tokenizer: The tokenizer for the model
        """
        self.model = model
        self.tokenizer = tokenizer
    
    def generate_text(self, prompt: str, 
                    generation_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The text prompt for generation
            generation_params: Parameters for text generation
            
        Returns:
            str: The generated text
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer must be set before generation")
        
        # Default generation parameters
        default_params = {
            "max_new_tokens": 200,
            "temperature": 0.5,
            "top_p": 0.92,
            "do_sample": True,
            "repetition_penalty": 1.3,
            "min_length": 100,
            "num_return_sequences": 1
        }
        
        # Override defaults with provided parameters
        if generation_params:
            default_params.update(generation_params)
        
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Set seed for reproducibility if needed
            if "seed" in default_params:
                torch.manual_seed(default_params.pop("seed"))
            
            # Add tokenizer-specific parameters
            if self.tokenizer.pad_token_id is not None:
                default_params["pad_token_id"] = self.tokenizer.pad_token_id
            if self.tokenizer.eos_token_id is not None:
                default_params["eos_token_id"] = self.tokenizer.eos_token_id
                
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    **default_params
                )
            
            # Decode the generated text
            if default_params.get("num_return_sequences", 1) > 1:
                # Return multiple sequences
                return [self.tokenizer.decode(output, skip_special_tokens=True) 
                        for output in outputs]
            else:
                # Return single sequence
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
        except Exception as e:
            logger.error(f"Error in text generation: {str(e)}")
            raise
    
    def extract_completion(self, full_text: str, prompt: str) -> str:
        """
        Extract the completion part from the full generated text.
        
        Args:
            full_text: The full generated text including prompt
            prompt: The original prompt
            
        Returns:
            str: The extracted completion
        """
        if full_text.startswith(prompt):
            return full_text[len(prompt):].strip()
        
        # If exact match fails, try to find the end of the prompt
        # This handles cases where tokenization/generation alters the prompt slightly
        prompt_end_idx = full_text.find(prompt[-20:])
        if prompt_end_idx != -1:
            prompt_end_idx += 20  # Length of the prompt fragment we searched for
            return full_text[prompt_end_idx:].strip()
            
        # If all else fails, return the full text (not ideal)
        logger.warning("Could not extract completion from generated text")
        return full_text
    
    def generate_multiple_variations(self, prompt: str, num_variations: int = 3, 
                                  generation_params: Optional[Dict[str, Any]] = None) -> list:
        """
        Generate multiple variations of text for the same prompt.
        
        Args:
            prompt: The text prompt for generation
            num_variations: Number of variations to generate
            generation_params: Parameters for text generation
            
        Returns:
            list: List of generated texts
        """
        variations = []
        
        # Default parameters
        params = generation_params.copy() if generation_params else {}
        params["num_return_sequences"] = 1  # Generate one at a time for diversity
        
        for i in range(num_variations):
            # Use different seeds for each variation
            params["seed"] = i + 42  # Arbitrary starting seed
            
            # Generate and extract completion
            full_text = self.generate_text(prompt, params)
            completion = self.extract_completion(full_text, prompt)
            variations.append(completion)
        
        return variations