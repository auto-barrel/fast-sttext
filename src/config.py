"""
Configuration module for the audiobook generator.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for audiobook generation."""

    # Google Cloud TTS settings
    DEFAULT_LANGUAGE_CODE = "pt-BR"
    DEFAULT_VOICE_GENDER = "FEMALE"
    DEFAULT_AUDIO_ENCODING = "MP3"
    DEFAULT_SPEAKING_RATE = 1.0
    DEFAULT_PITCH = 0.0
    DEFAULT_VOLUME_GAIN_DB = 0.0

    # Audio processing settings
    CHUNK_SIZE = 5000  # Maximum characters per TTS request
    PAUSE_BETWEEN_SENTENCES = 800  # milliseconds
    PAUSE_BETWEEN_PARAGRAPHS = 1500  # milliseconds
    PAUSE_BETWEEN_CHAPTERS = 3000  # milliseconds

    # File settings
    INPUT_DIR = "input"
    OUTPUT_DIR = "output"
    SUPPORTED_TEXT_FORMATS = [".txt", ".md"]
    SUPPORTED_EBOOK_FORMATS = [".epub", ".pdf"]

    # Voice options
    VOICE_OPTIONS = {
        "pt-BR": {
            "FEMALE": ["pt-BR-Wavenet-A", "pt-BR-Wavenet-C", "pt-BR-Standard-A"],
            "MALE": ["pt-BR-Wavenet-B", "pt-BR-Standard-B"],
        },
        "en-US": {
            "FEMALE": ["en-US-Wavenet-C", "en-US-Wavenet-E", "en-US-Standard-C"],
            "MALE": ["en-US-Wavenet-A", "en-US-Wavenet-D", "en-US-Standard-B"],
        },
    }

    @classmethod
    def get_voice_name(
        cls, language_code: str, gender: str, premium: bool = True
    ) -> str:
        """Get appropriate voice name based on language and gender."""
        voices = cls.VOICE_OPTIONS.get(language_code, {}).get(gender, [])
        if not voices:
            return None

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
