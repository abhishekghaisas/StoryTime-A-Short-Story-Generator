"""
Post-Processor module for story generation.

Handles various post-processing and quality enhancement tasks
for generated stories.
"""

import re
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

class PostProcessor:
    """Handles post-processing and quality enhancement for generated stories."""
    
    def __init__(self):
        """Initialize the post-processor."""
        pass
    
    def process_story(self, story: str, prefix: str = "Once upon a time, ") -> str:
        """
        Apply all post-processing steps to a generated story.
        
        Args:
            story: The story text to process
            prefix: The prefix to preserve in the story
            
        Returns:
            str: The processed story
        """
        try:
            # Fix encoding issues
            story = self.fix_encoding_issues(story)
            
            # Fix story ending
            story = self.fix_story_ending(story)
            
            # Ensure character consistency
            story = self.ensure_character_consistency(story)
            
            # Clean text
            story = self.clean_text(story)
            
            # Make sure the story has the correct prefix
            if not story.startswith(prefix):
                story = prefix + story
            
            return story
            
        except Exception as e:
            logger.error(f"Error in post-processing: {str(e)}")
            # Return original story if processing fails
            return story
    
    def fix_encoding_issues(self, text: str) -> str:
        """
        Fix common encoding issues in generated text.
        
        Args:
            text: The text to process
            
        Returns:
            str: Text with encoding issues fixed
        """
        replacements = {
            "â€™": "'",
            "â€œ": "\"",
            "â€": "\"",
            "&quot;": "\"",
            "&nbsp;": " ",
            "\\n": " "
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text
    
    def fix_story_ending(self, story: str) -> str:
        """
        Ensure the story has a proper ending.
        
        Args:
            story: The story text
            
        Returns:
            str: Story with proper ending
        """
        # If the story doesn't end with punctuation, find the last sentence end
        if story and not any(story.strip().endswith(end) for end in ['.', '!', '?']):
            last_sentence_end = max(story.rfind('.'), story.rfind('!'), story.rfind('?'))
            if last_sentence_end > 0:
                story = story[:last_sentence_end + 1]
        return story
    
    def extract_characters(self, story: str) -> Dict[str, List[int]]:
        """
        Extract the main characters from a story with their sentence positions.
        
        Args:
            story: The story text
            
        Returns:
            dict: Dictionary of characters and their positions
        """
        sentences = re.split(r'[.!?] ', story)
        words_by_sentence = [s.split() for s in sentences]
        
        # Find potential characters (capitalized words not at start of sentences)
        characters = {}
        for i, sentence_words in enumerate(words_by_sentence):
            for j, word in enumerate(sentence_words):
                # Look for capitalized words that aren't at the start of sentences
                if (j > 0 or i > 0) and len(word) > 2 and word[0].isupper() and word.isalpha():
                    if word not in characters:
                        characters[word] = []
                    characters[word].append(i)
        
        # Filter to include only characters mentioned multiple times
        main_characters = {char: occurrences for char, occurrences in characters.items() 
                          if len(occurrences) > 1}
        
        return main_characters
    
    def ensure_character_consistency(self, story: str) -> str:
        """
        Check and improve character consistency in the story.
        
        Args:
            story: The story text
            
        Returns:
            str: Story with improved character consistency
        """
        # Extract characters
        main_characters = self.extract_characters(story)
        
        # If no significant characters, return the original story
        if not main_characters:
            return story
        
        # Story is too short to worry about character consistency
        if len(re.split(r'[.!?] ', story)) < 5:
            return story
        
        # Fix common gender inconsistency issues
        gender_pairs = [
            ("he", "she"), ("him", "her"), ("his", "her"),
            ("boy", "girl"), ("man", "woman"), ("son", "daughter"),
            ("brother", "sister"), ("prince", "princess"),
            ("king", "queen"), ("father", "mother")
        ]
        
        # Check for gender confusion in the story
        for male, female in gender_pairs:
            # If both male and female forms are found
            if (male.lower() in story.lower() and female.lower() in story.lower()):
                # Count occurrences to determine dominant gender
                male_count = sum(1 for word in story.lower().split() 
                                if word == male.lower() or word == male.lower() + ',' 
                                or word == male.lower() + '.')
                female_count = sum(1 for word in story.lower().split() 
                                  if word == female.lower() or word == female.lower() + ',' 
                                  or word == female.lower() + '.')
                
                # Only correct if there's a clear dominant gender (3x more occurrences)
                if male_count > female_count * 3:  # Male is dominant
                    story = re.sub(r'\b' + female + r'\b', male, story, flags=re.IGNORECASE)
                elif female_count > male_count * 3:  # Female is dominant
                    story = re.sub(r'\b' + male + r'\b', female, story, flags=re.IGNORECASE)
                
                # Don't correct if it's more balanced
        
        # Check for name inconsistencies - too complex for simple fixes
        # This would require more advanced NLP techniques
        
        return story
    
    def clean_text(self, text: str) -> str:
        """
        General text cleaning for improved readability.
        
        Args:
            text: The text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove any repeated spaces
        text = re.sub(r' +', ' ', text)
        
        # Fix any strange punctuation patterns
        text = re.sub(r'\.{2,}', '...', text)  # Replace multiple periods with ellipsis
        
        # Fix common punctuation mistakes
        text = re.sub(r' ,', ',', text)  # Remove space before comma
        text = re.sub(r' \.', '.', text)  # Remove space before period
        text = re.sub(r' !', '!', text)   # Remove space before exclamation
        text = re.sub(r' \?', '?', text)  # Remove space before question mark
        
        # Ensure spaces after punctuation
        text = re.sub(r'([.!?]),', r'\1 ', text)
        
        return text.strip()
    
from sentence_transformers import SentenceTransformer, util
import re

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def check_and_correct_title(story_text: str, current_title: str, similarity_threshold=0.55) -> str:
    """
    Checks whether the title is semantically coherent with the story.
    If not, generates a corrected title.
    
    Args:
        story_text (str): The generated story.
        current_title (str): The title to evaluate.
        similarity_threshold (float): Cosine similarity cutoff below which title is replaced.

    Returns:
        str: Either the original title (if good) or a new corrected title.
    """
    # Preprocess inputs
    story = story_text.strip().replace('\n', ' ')
    title = current_title.strip()

    # Calculate embeddings
    story_embedding = model.encode(story, convert_to_tensor=True)
    title_embedding = model.encode(title, convert_to_tensor=True)

    similarity = util.cos_sim(story_embedding, title_embedding).item()

    if similarity >= similarity_threshold:
        return title  # Title is coherent enough

    # If not coherent, generate a new one (basic rule-based for now)
    # Heuristic: Use first sentence of the story, clean it up
    first_line = re.split(r'[.!?]', story)[0]
    corrected_title = first_line.strip().capitalize()
return corrected_title

    # Ensure it's not too long
    if len(corrected_title.split()) > 10:
        corrected_title = "A short story about " + corrected_title.split()[0].lower()
