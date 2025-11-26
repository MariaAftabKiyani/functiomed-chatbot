"""
Query Normalizer for RAG Retrieval Pipeline
Cleans and standardizes user queries with language detection.
"""
import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NormalizedQuery:
    """Result of query normalization"""
    original: str
    normalized: str
    detected_language: Optional[str]
    char_count: int
    was_modified: bool
    
    def __repr__(self):
        return f"NormalizedQuery(lang={self.detected_language}, modified={self.was_modified})"


class QueryNormalizer:
    """
    Normalize and clean user queries for embedding and retrieval.
    
    Features:
    - Whitespace normalization
    - Special character handling
    - Language detection (DE/EN)
    - Length validation
    """
    
    def __init__(self, max_length: int = 512):
        """
        Initialize query normalizer.
        
        Args:
            max_length: Maximum allowed query length in characters
        """
        self.max_length = max_length
        
        # German-specific words for language detection
        self.german_indicators = {
            'der', 'die', 'das', 'und', 'ist', 'von', 'für', 'mit', 'auf',
            'eine', 'einem', 'einen', 'welche', 'welcher', 'welches',
            'funktioniert', 'bietet', 'kostet', 'können', 'möchte'
        }

        # English-specific words
        self.english_indicators = {
            'the', 'and', 'is', 'for', 'with', 'what', 'how', 'can', 'does',
            'which', 'where', 'when', 'why', 'offer', 'cost', 'provide'
        }

        # French-specific words
        self.french_indicators = {
            'le', 'la', 'les', 'un', 'une', 'des', 'et', 'est', 'de', 'pour',
            'avec', 'que', 'qui', 'quoi', 'comment', 'quand', 'où', 'pourquoi',
            'offre', 'coût', 'fournir', 'quel', 'quelle'
        }
        
        logger.info(f"QueryNormalizer initialized (max_length={max_length})")
    
    def normalize(self, query: str) -> NormalizedQuery:
        """
        Normalize a user query.
        
        Args:
            query: Raw user input
            
        Returns:
            NormalizedQuery object with cleaned text and metadata
            
        Raises:
            ValueError: If query is empty or too long
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        original = query
        normalized = query
        
        # Step 1: Basic whitespace cleanup
        normalized = self._clean_whitespace(normalized)
        
        # Step 2: Remove excessive punctuation
        normalized = self._clean_punctuation(normalized)
        
        # Step 3: Normalize case (preserve for language detection first)
        detected_language = self._detect_language(normalized)
        normalized = normalized.strip()
        
        # Step 4: Validate length
        if len(normalized) > self.max_length:
            logger.warning(f"Query too long ({len(normalized)} chars), truncating to {self.max_length}")
            normalized = normalized[:self.max_length].strip()
        
        # Check if modified
        was_modified = (normalized != original.strip())
        
        result = NormalizedQuery(
            original=original,
            normalized=normalized,
            detected_language=detected_language,
            char_count=len(normalized),
            was_modified=was_modified
        )
        
        logger.debug(f"Normalized query: {result}")
        return result
    
    def _clean_whitespace(self, text: str) -> str:
        """Normalize whitespace (spaces, tabs, newlines)"""
        # Replace all whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _clean_punctuation(self, text: str) -> str:
        """Clean excessive or problematic punctuation"""
        # Remove multiple consecutive punctuation marks (keep single)
        text = re.sub(r'([?.!,;:]){2,}', r'\1', text)
        
        # Remove leading/trailing punctuation except question marks
        text = re.sub(r'^[.,;:!]+', '', text)
        text = re.sub(r'[.,;:!]+$', '', text)
        
        return text
    
    def _detect_language(self, text: str) -> Optional[str]:
        """
        Detect query language (DE, EN, or FR).

        Simple heuristic: count language-specific indicator words.
        Returns None if uncertain.
        """
        # Convert to lowercase for detection
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Count indicators
        german_count = len(words & self.german_indicators)
        english_count = len(words & self.english_indicators)
        french_count = len(words & self.french_indicators)

        # Decision logic - highest score wins
        max_count = max(german_count, english_count, french_count)

        if max_count == 0:
            # Check for umlauts (strong German indicator)
            if re.search(r'[äöüÄÖÜß]', text):
                return "DE"
            # Check for French accents
            if re.search(r'[àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]', text):
                return "FR"
            return None  # Uncertain

        if german_count == max_count:
            return "DE"
        elif english_count == max_count:
            return "EN"
        elif french_count == max_count:
            return "FR"

        return None
    
    def validate_length(self, query: str) -> bool:
        """Check if query length is acceptable"""
        return 0 < len(query.strip()) <= self.max_length


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s'
    )
    
    normalizer = QueryNormalizer(max_length=512)
    
    # Test cases
    test_queries = [
        "Welche Therapien bietet functiomed an?",
        "  What   treatments   do you offer?  ",
        "Physiotherapie...!!!",
        "Wie funktioniert die Akupunktur bei functiomed",
        "How much does physiotherapy cost???",
        "   " + "x" * 600,  # Too long
    ]
    
    print("\n" + "="*70)
    print("QUERY NORMALIZER TEST")
    print("="*70)
    
    for query in test_queries:
        print(f"\nOriginal: '{query[:50]}...'")
        try:
            result = normalizer.normalize(query)
            print(f"Normalized: '{result.normalized[:50]}...'")
            print(f"Language: {result.detected_language}")
            print(f"Modified: {result.was_modified}")
            print(f"Length: {result.char_count} chars")
        except ValueError as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "="*70)