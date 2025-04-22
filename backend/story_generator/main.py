"""
Main Story Generator module.

Integrates all components of the story generation system.
"""
import os
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_parent_dir)

import torch
import logging
from typing import Dict, Any, Optional, List, Tuple

from backend.story_generator.model_manager import ModelManager
from backend.story_generator.prompt_engine import PromptEngine
from backend.story_generator.text_generator import TextGenerator
from backend.story_generator.post_processor import PostProcessor
from backend.utils.quality_checker import QualityChecker
from backend.utils.memory_utils import log_memory_usage, clear_gpu_memory

logger = logging.getLogger(__name__)

class StoryGenerator:
    """
    Main class for generating bedtime stories.
    Integrates model management, prompt creation, text generation, and post-processing.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize the story generator with a model path.
        
        Args:
            model_path: Path to the fine-tuned model
        """
        self.model_manager = ModelManager()
        self.prompt_engine = PromptEngine()
        self.text_generator = TextGenerator()
        self.post_processor = PostProcessor()
        self.quality_checker = QualityChecker()
        self.model_path = model_path
        
        # Load the model
        model, tokenizer = self.model_manager.load_model(model_path)
        self.text_generator.set_model_and_tokenizer(model, tokenizer)
        
        # Log memory usage after loading
        log_memory_usage()
    
    def generate_story(self, theme: str, genre: str, max_length: int = 200, 
                     temperature: float = 0.5) -> str:
        """
        Generate a bedtime story based on theme and genre.
        
        Args:
            theme: Theme of the story (e.g., "animals", "space")
            genre: Genre of the story (e.g., "adventure", "fantasy")
            max_length: Maximum length of the generated story
            temperature: Temperature for generation (lower = more consistent)
            
        Returns:
            str: The generated story
        """
        try:
            logger.info(f"Generating {genre} story about {theme}...")
            
            # Optimize prompt for theme and genre
            # This will automatically select the best prompt template and parameters
            constraint_level = 1.0 - temperature  # Convert temperature to constraint level
            optimized_params = self.prompt_engine.optimize_prompt(theme, genre, constraint_level)
            
            # Create prompt using the optimized template
            opening_phrase = "Once upon a time, "
            template_type = optimized_params.pop("template_type")
            prompt = self.prompt_engine.create_prompt(
                theme=theme,
                genre=genre,
                template_type=template_type,
                opening=opening_phrase
            )
            
            # Set up generation parameters
            generation_params = {
                "max_new_tokens": max_length,
                "temperature": optimized_params.get("temperature", temperature),
                "top_p": optimized_params.get("top_p", 0.92),
                "do_sample": True,
                "repetition_penalty": optimized_params.get("repetition_penalty", 1.3),
                "min_length": 100
            }
            
            # Generate the story
            full_text = self.text_generator.generate_text(prompt, generation_params)
            
            # Extract just the generated part
            story = self.text_generator.extract_completion(full_text, prompt)
            
            # Apply post-processing
            processed_story = self.post_processor.process_story(story, opening_phrase)
            
            # Clear GPU memory if needed
            if torch.cuda.is_available() and torch.cuda.memory_allocated() / torch.cuda.get_device_properties(0).total_memory > 0.8:
                logger.info("High GPU memory usage detected, clearing cache...")
                clear_gpu_memory()
            
            return processed_story
            
        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            # Return a fallback story if generation fails
            return f"{opening_phrase}there was a magical land where {theme} and {genre} stories were told. [Error: Could not generate full story]"
    
    def generate_title(self, story: str) -> str:
        """
        Generate a title for the story.
        
        Args:
            story: The story text
            
        Returns:
            str: Generated title
        """
        try:
            # Extract key themes from the story
            words = story.split()
            
            # Find the first few words after "Once upon a time"
            intro_index = story.lower().find("once upon a time")
            if intro_index >= 0:
                start_idx = intro_index + 16  # Length of "once upon a time"
                first_part = story[start_idx:start_idx + 50]  # Take a chunk after the intro
                
                # Find the first noun or interesting part
                title_words = []
                for word in first_part.split()[:5]:
                    # Look for capitalized words or long words
                    if word[0].isupper() or len(word) > 4:
                        title_words.append(word)
                
                if title_words:
                    # Clean up the words
                    title_words = [word.strip(',.!?;:') for word in title_words]
                    title = " ".join(title_words).strip()
                    return "The " + title.title()
            
            # Fallback if we can't extract from beginning
            if len(words) > 5:
                # Simple approach - get a few key words
                for i in range(min(20, len(words))):
                    if words[i][0].isupper() and len(words[i]) > 3:
                        return f"The {words[i]}'s Adventure"
            
            # Default title if all else fails
            return "A Magical Bedtime Story"
            
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return "A Bedtime Story"
    
    def evaluate_quality(self, story: str) -> Dict[str, Any]:
        """
        Evaluate the quality of a generated story.
        
        Args:
            story: The story text
            
        Returns:
            dict: Quality assessment
        """
        try:
            return self.quality_checker.check_story_quality(story)
        except Exception as e:
            logger.error(f"Error evaluating story quality: {str(e)}")
            # Return basic quality assessment if evaluation fails
            return {
                "score": 5,  # Neutral score
                "issues": [f"Could not fully evaluate quality: {str(e)}"],
                "word_count": len(story.split()),
                "classification": "Acceptable"
            }