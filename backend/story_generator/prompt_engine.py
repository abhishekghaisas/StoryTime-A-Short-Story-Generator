"""
Prompt Engine module for story generation.

Handles creation of prompts for the story generator.
Optimizes prompts for different themes, genres and requirements.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PromptEngine:
    """Creates and optimizes prompts for story generation."""
    
    def __init__(self):
        """Initialize the prompt engine."""
        # Base templates for different types of prompts
        self.templates = {
            "standard": "Write a short bedtime story for a young child about {theme} in the style of a {genre} tale.\n\nStory: {opening}",
            
            "enhanced": """Write a short bedtime story for a young child about {theme} in the style of a {genre} tale.
The story should have a clear beginning, middle, and end with consistent characters throughout. It should be simple, engaging, and have a positive message.

Story: {opening}""",
            
            "character_focused": """Write a short bedtime story for a young child about {theme} in the style of a {genre} tale.
The main characters should remain consistent throughout the story.
The story should have a clear arc with a beginning, middle, and end.

Story: {opening}""",
            
            "educational": """Write a short, educational bedtime story for a young child about {theme} in the style of a {genre} tale.
Include a simple lesson or message that's appropriate for children.
The story should be engaging and easy to understand.

Story: {opening}"""
        }
    
    def create_prompt(self, theme: str, genre: str, template_type: str = "enhanced", 
                    opening: str = "Once upon a time, ", 
                    additional_guidance: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a prompt for story generation.
        
        Args:
            theme: Theme of the story
            genre: Genre of the story
            template_type: Type of template to use
            opening: Opening words for the story
            additional_guidance: Additional parameters to include in the prompt
            
        Returns:
            str: The complete prompt
        """
        # Get the base template
        if template_type not in self.templates:
            logger.warning(f"Template type '{template_type}' not found, defaulting to 'standard'")
            template_type = "standard"
        
        template = self.templates[template_type]
        
        # Format with basic parameters
        prompt = template.format(
            theme=theme,
            genre=genre,
            opening=opening
        )
        
        # Add any additional guidance if provided
        if additional_guidance:
            custom_guidance = "\n".join([f"{key}: {value}" for key, value in additional_guidance.items()])
            prompt = f"{prompt}\n\nAdditional guidance:\n{custom_guidance}"
        
        logger.debug(f"Created prompt with template '{template_type}'")
        return prompt
    
    def optimize_for_theme(self, theme: str) -> str:
        """
        Determine the best template type for a given theme.
        
        Args:
            theme: Theme of the story
            
        Returns:
            str: Recommended template type
        """
        # Theme-specific optimization
        educational_themes = ["animals", "space", "ocean", "seasons", "weather"]
        character_themes = ["friendship", "family", "toys"]
        
        if theme in educational_themes:
            return "educational"
        elif theme in character_themes:
            return "character_focused"
        else:
            return "enhanced"
    
    def optimize_for_genre(self, genre: str) -> str:
        """
        Determine the best template type for a given genre.
        
        Args:
            genre: Genre of the story
            
        Returns:
            str: Recommended template type
        """
        # Genre-specific optimization
        educational_genres = ["educational", "fable"]
        character_genres = ["adventure", "mystery"]
        
        if genre in educational_genres:
            return "educational"
        elif genre in character_genres:
            return "character_focused"
        else:
            return "enhanced"
    
    def optimize_prompt(self, theme: str, genre: str, 
                       constraint_level: float = 0.5) -> Dict[str, Any]:
        """
        Intelligently select the best prompt template and parameters.
        
        Args:
            theme: Theme of the story
            genre: Genre of the story
            constraint_level: How constrained the generation should be (0.0-1.0)
            
        Returns:
            Dict: Optimized parameters for story generation
        """
        # Determine best template based on theme and genre
        theme_template = self.optimize_for_theme(theme)
        genre_template = self.optimize_for_genre(genre)
        
        # Choose the more specific template
        if theme_template == "educational" or genre_template == "educational":
            template_type = "educational"
        elif theme_template == "character_focused" or genre_template == "character_focused":
            template_type = "character_focused"
        else:
            template_type = "enhanced"
        
        # Adjust generation parameters based on constraint level
        # Higher constraint = more predictable, consistent stories
        temperature = max(0.1, 0.8 - (constraint_level * 0.6))  # 0.2 to 0.8
        top_p = min(0.95, 0.7 + (constraint_level * 0.25))      # 0.7 to 0.95
        repetition_penalty = 1.0 + (constraint_level * 0.5)     # 1.0 to 1.5
        
        # Return optimized parameters
        return {
            "template_type": template_type,
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty
        }