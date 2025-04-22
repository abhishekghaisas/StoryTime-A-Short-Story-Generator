"""
Quality Checker module for story evaluation.

Provides tools for assessing the quality of generated stories.
"""

import re
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

class QualityChecker:
    """Evaluates the quality of generated stories."""
    
    def __init__(self):
        """Initialize the quality checker."""
        pass
    
    def check_story_quality(self, story: str) -> Dict[str, Any]:
        """
        Perform a comprehensive quality check on a story.
        
        Args:
            story: The story text to evaluate
            
        Returns:
            dict: Quality assessment results
        """
        # Initialize quality metrics
        quality = {
            "score": 10,           # Start with perfect score
            "issues": [],          # List of identified issues
            "word_count": len(story.split()),
            "classification": "Excellent"  # Overall quality classification
        }
        
        # Check length
        if quality["word_count"] < 50:
            quality["score"] -= 3
            quality["issues"].append("Story is too short")
        elif quality["word_count"] < 100:
            quality["score"] -= 1
            quality["issues"].append("Story could be longer")
        
        # Check for encoding issues
        if any(marker in story for marker in ['â€™', 'â€œ', 'â€']):
            quality["score"] -= 1
            quality["issues"].append("Contains encoding issues")
        
        # Check for proper ending
        if not any(story.strip().endswith(end) for end in ['.', '!', '?']):
            quality["score"] -= 1
            quality["issues"].append("Missing proper ending")
        
        # Check for repetition
        repetition_issue = self.check_repetition(story)
        if repetition_issue:
            quality["score"] -= 2
            quality["issues"].append(repetition_issue)
        
        # Check for character consistency
        is_consistent, consistency_message = self.check_character_consistency(story)
        if not is_consistent:
            quality["score"] -= 2
            quality["issues"].append(consistency_message)
        
        # Check for narrative structure
        has_structure, structure_message = self.check_narrative_structure(story)
        if not has_structure:
            quality["score"] -= 1
            quality["issues"].append(structure_message)
        
        # Set classification based on score
        if quality["score"] >= 9:
            quality["classification"] = "Excellent"
        elif quality["score"] >= 7:
            quality["classification"] = "Good"
        elif quality["score"] >= 5:
            quality["classification"] = "Acceptable"
        else:
            quality["classification"] = "Poor"
            
        # If no issues, note that
        if not quality["issues"]:
            quality["issues"] = ["No issues detected"]
        
        return quality
    
    def check_repetition(self, story: str) -> str:
        """
        Check for repetitive content in the story.
        
        Args:
            story: The story text
            
        Returns:
            str: Description of repetition issue or empty string
        """
        sentences = [s.strip() for s in re.split(r'[.!?] ', story) if s.strip()]
        
        # Check for exactly repeated sentences
        for i in range(len(sentences)-1):
            if sentences[i] == sentences[i+1]:
                return "Contains consecutive repeated sentences"
        
        # Check for repeated sentence beginnings
        sentence_beginnings = [' '.join(s.split()[:3]) for s in sentences if len(s.split()) >= 3]
        beginning_counts = {}
        
        for beginning in sentence_beginnings:
            beginning_counts[beginning] = beginning_counts.get(beginning, 0) + 1
            
        repetitive_beginnings = [b for b, c in beginning_counts.items() if c >= 3]
        if repetitive_beginnings:
            return f"Repetitive sentence beginnings: '{repetitive_beginnings[0]}...'"
        
        # Check for excessive use of certain words or phrases
        words = story.lower().split()
        word_counts = {}
        
        for word in words:
            if len(word) > 3:  # Only count significant words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Identify words used excessively (more than 5% of total words and at least 5 times)
        threshold = max(5, int(len(words) * 0.05))
        overused_words = [w for w, c in word_counts.items() if c >= threshold and c >= 5]
        
        if overused_words:
            return f"Overuse of word: '{overused_words[0]}'"
        
        return ""
    
    def check_character_consistency(self, story: str) -> Tuple[bool, str]:
        """
        Check character consistency throughout the story.
        
        Args:
            story: The story text
            
        Returns:
            tuple: (is_consistent, message)
        """
        # Extract potential character names
        sentences = re.split(r'[.!?] ', story)
        words_by_sentence = [s.split() for s in sentences]
        
        # Find characters (capitalized words not at start of sentences)
        characters = {}
        for i, sentence_words in enumerate(words_by_sentence):
            for j, word in enumerate(sentence_words):
                if (j > 0 or i > 0) and len(word) > 2 and word[0].isupper() and word.isalpha():
                    if word not in characters:
                        characters[word] = []
                    characters[word].append(i)
        
        # Only consider frequent characters (mentioned at least twice)
        main_characters = {char: occurrences for char, occurrences in characters.items() 
                          if len(occurrences) > 1}
        
        # Story is too short to worry about character consistency
        if len(sentences) < 5:
            return True, "Story too short for character analysis"
            
        # Not enough recurring characters
        if not main_characters:
            return True, "No recurring characters detected"
            
        # Split into thirds to check for character presence across sections
        thirds = [len(sentences)//3, 2*len(sentences)//3]
        
        # Check if characters appear in beginning and end but not middle
        inconsistent_chars = []
        for char, occurrences in main_characters.items():
            has_begin = any(i < thirds[0] for i in occurrences)
            has_middle = any(thirds[0] <= i < thirds[1] for i in occurrences)
            has_end = any(i >= thirds[1] for i in occurrences)
            
            if has_begin and has_end and not has_middle:
                inconsistent_chars.append(char)
        
        if inconsistent_chars:
            return False, f"Characters abandoned in middle: {', '.join(inconsistent_chars)}"
        
        return True, "Character consistency maintained"
    
    def check_narrative_structure(self, story: str) -> Tuple[bool, str]:
        """
        Check if the story has proper narrative structure.
        
        Args:
            story: The story text
            
        Returns:
            tuple: (has_structure, message)
        """
        # Simple heuristic based on length
        if len(story.split()) < 75:
            return False, "Story too short for proper structure"
        
        # Split into beginning, middle, end
        sentences = [s.strip() for s in re.split(r'[.!?] ', story) if s.strip()]
        
        if len(sentences) < 6:
            return False, "Too few sentences for proper structure"
        
        # Check for key structural elements
        has_setting = False
        has_problem = False
        has_resolution = False
        
        # Setting indicators
        setting_markers = ["was", "were", "lived", "once", "upon", "time", "long ago", "far away"]
        problem_markers = ["but", "however", "suddenly", "problem", "couldn't", "wanted", "needed"]
        resolution_markers = ["finally", "solved", "learned", "happy", "together", "end", "from then on"]
        
        # Check first third for setting
        first_third = ' '.join(sentences[:len(sentences)//3]).lower()
        for marker in setting_markers:
            if marker in first_third:
                has_setting = True
                break
        
        # Check middle third for problem/conflict
        middle_third = ' '.join(sentences[len(sentences)//3:2*len(sentences)//3]).lower()
        for marker in problem_markers:
            if marker in middle_third:
                has_problem = True
                break
        
        # Check last third for resolution
        last_third = ' '.join(sentences[2*len(sentences)//3:]).lower()
        for marker in resolution_markers:
            if marker in last_third:
                has_resolution = True
                break
        
        # Determine overall structure
        if has_setting and has_problem and has_resolution:
            return True, "Complete narrative structure"
        elif has_setting and has_resolution:
            return True, "Basic narrative structure present"
        else:
            missing_elements = []
            if not has_setting:
                missing_elements.append("clear setting")
            if not has_problem:
                missing_elements.append("conflict/problem")
            if not has_resolution:
                missing_elements.append("resolution")
                
            return False, f"Missing narrative elements: {', '.join(missing_elements)}"