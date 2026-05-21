"""
Language detection service
Supports English, Hindi, Tamil and Telugu
"""
import os
from typing import Tuple
from textblob import TextBlob
import json

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
}

# Simple character-based detection for Hindi, Tamil and Telugu
HINDI_CHARS = set(chr(i) for i in range(0x0900, 0x097F))  # Devanagari
TAMIL_CHARS = set(chr(i) for i in range(0x0B80, 0x0C00))  # Tamil
TELUGU_CHARS = set(chr(i) for i in range(0x0C00, 0x0C80))  # Telugu

class LanguageDetectionService:
    """Language detection service"""
    
    @staticmethod
    def detect_language(text: str) -> Tuple[str, float]:
        """
        Detect language from text
        Returns (language_code, confidence)
        """
        if not text or len(text.strip()) < 2:
            return "en", 0.5

        # Count language-specific characters
        hindi_count = sum(1 for char in text if char in HINDI_CHARS)
        tamil_count = sum(1 for char in text if char in TAMIL_CHARS)
        telugu_count = sum(1 for char in text if char in TELUGU_CHARS)

        total_chars = len(text)

        # Heuristic thresholds: if >30% characters belong to a script, choose that language
        if hindi_count / total_chars > 0.3:
            return "hi", min(1.0, hindi_count / total_chars)

        if tamil_count / total_chars > 0.3:
            return "ta", min(1.0, tamil_count / total_chars)

        if telugu_count / total_chars > 0.3:
            return "te", min(1.0, telugu_count / total_chars)

        # Default to English for Latin characters
        return "en", 0.9

    @staticmethod
    def validate_language(language_code: str) -> bool:
        """Validate if language is supported"""
        return language_code in SUPPORTED_LANGUAGES

    @staticmethod
    def get_language_name(language_code: str) -> str:
        """Get language name from code"""
        return SUPPORTED_LANGUAGES.get(language_code, "Unknown")
