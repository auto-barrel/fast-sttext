"""
Configuration module for the audiobook generator.
"""

import logging
import os


class Config:
    """Configuration class for audiobook generation."""

    # Google Cloud TTS settings
    DEFAULT_LANGUAGE_CODE = "pt-BR"
    DEFAULT_VOICE_GENDER = "FEMALE"
    DEFAULT_AUDIO_ENCODING = "MP3"
    DEFAULT_SPEAKING_RATE = 0.95
    DEFAULT_PITCH = 0.0
    PAUSE_BETWEEN_SENTENCES = 800  # milliseconds
    PAUSE_BETWEEN_PARAGRAPHS = 2000  # milliseconds
    PAUSE_BETWEEN_CHAPTERS = 3000  # milliseconds

    DEFAULT_VOLUME_GAIN_DB = 0.3
    # Audio processing settings - Updated for optimal API usage
    CHUNK_SIZE = 3500  # Conservative for 4000 byte limit
    # Alternative: CHUNK_SIZE = 3500  # For actual 5000 byte API limit
    MAX_API_BYTES = 4000  # Your target limit (API supports 5000)

    # File settings
    INPUT_DIR = "input"
    OUTPUT_DIR = "output"
    SUPPORTED_TEXT_FORMATS = [".txt", ".md"]
    SUPPORTED_EBOOK_FORMATS = [".epub", ".pdf"]
    # Voice options
    VOICE_OPTIONS = {
        "pt-BR": {
            "FEMALE": ["pt-BR-Wavenet-C", "pt-BR-Wavenet-A", "pt-BR-Standard-A"],
            "MALE": ["pt-BR-Wavenet-B", "pt-BR-Standard-B"],
        },
        "en-US": {
            "FEMALE": ["en-US-Wavenet-C", "en-US-Wavenet-E", "en-US-Standard-C"],
            "MALE": ["en-US-Wavenet-A", "en-US-Wavenet-D", "en-US-Standard-B"],
        },
    }

    @classmethod
    def get_voice_name(cls, language_code: str, gender: str, premium: bool = True) -> str:
        """Get appropriate voice name based on language and gender."""
        voices = cls.VOICE_OPTIONS.get(language_code, {}).get(gender, [])
        if not voices:
            logging.warning("No voices avaliable, check VOICE_OPTIONS")
            return "None"

        # Prefer Wavenet (premium) voices if available
        if premium:
            wavenet_voices = [v for v in voices if "Wavenet" in v]
            if wavenet_voices:
                return wavenet_voices[0]

        # Fallback to standard voices
        standard_voices = [v for v in voices if "Standard" in v]
        return standard_voices[0] if standard_voices else voices[0]

    @classmethod
    def get_output_path(cls, filename: str) -> str:
        """Get full output path for a filename."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        return os.path.join(cls.OUTPUT_DIR, filename)

    @classmethod
    def get_input_path(cls, filename: str) -> str:
        """Get full input path for a filename."""
        return os.path.join(cls.INPUT_DIR, filename)

    @classmethod
    def _validate_chunk_size(cls, text: str) -> bool:
        """
        Validate if text chunk will fit within API limits.

        Args:
            text: Text to validate

        Returns:
            True if chunk is within limits
        """
        estimated_size = cls.__estimate_ssml_size(text)
        return estimated_size <= cls.MAX_API_BYTES

    @classmethod
    def __estimate_ssml_size(cls, text: str) -> int:
        """Estimate SSML size in bytes."""
        import re

        sentence_count = len(re.findall(r"[.!?]+", text))
        number_count = len(re.findall(r"\b\d+\b", text))
        base_size = len(text.encode("utf-8"))

        ssml_overhead = 15 + (sentence_count * 25) + (number_count * 35)
        return base_size + ssml_overhead
