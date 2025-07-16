import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

from google.api_core import exceptions
from google.cloud import texttospeech

from .config import Config
from .text_processor import TextSegment

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSEngine:
    """Enhanced Text-to-Speech engine with better error handling and features."""

    def __init__(
        self,
        language_code: Optional[str] = None,
        voice_gender: Optional[str] = None,
        use_premium_voices: bool = True,
    ):
        """
        Initialize TTS engine.

        Args:
            language_code: Language code (e.g., "pt-BR", "en-US")
            voice_gender: Voice gender (MALE, FEMALE, NEUTRAL)
            use_premium_voices: Whether to use premium Wavenet voices
        """
        self.language_code = language_code or Config.DEFAULT_LANGUAGE_CODE
        self.voice_gender = voice_gender or Config.DEFAULT_VOICE_GENDER
        self.use_premium_voices = use_premium_voices

        # Initialize client
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("TTS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS client: {e}")
            raise

        # Get voice configuration
        self.voice_name = Config.get_voice_name(
            self.language_code, self.voice_gender, self.use_premium_voices
        )

        logger.info(f"Using voice: {self.voice_name or 'default'}")

    def list_available_voices(self) -> List[Dict]:
        """List all available voices for the current language."""
        try:
            voices = self.client.list_voices()
            available_voices = []

            for voice in voices.voices:
                if self.language_code in voice.language_codes:
                    available_voices.append(
                        {
                            "name": voice.name,
                            "gender": voice.ssml_gender.name,
                            "language_codes": list(voice.language_codes),
                            "natural_sample_rate": voice.natural_sample_rate_hertz,
                        }
                    )

            return available_voices
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []

    def synthesize_text(
        self,
        text: str,
        output_filename: Optional[str] = None,
        use_ssml: bool = False,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
    ) -> bytes:
        """
        Convert text to speech and optionally save to file.

        Args:
            text: Text to synthesize
            output_filename: Output file path (optional)
            use_ssml: Whether the text contains SSML markup
            speaking_rate: Speaking rate (0.25 to 4.0)
            pitch: Pitch (-20.0 to 20.0)
            volume_gain_db: Volume gain (-96.0 to 16.0)

        Returns:
            Audio content as bytes
        """
        try:
            # Prepare synthesis input
            if use_ssml:
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)

            # Voice selection
            voice_params = {
                "language_code": self.language_code,
                "ssml_gender": getattr(texttospeech.SsmlVoiceGender, self.voice_gender),
            }

            if self.voice_name:
                voice_params["name"] = self.voice_name

            voice = texttospeech.VoiceSelectionParams(**voice_params)

            # Audio configuration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch,
                volume_gain_db=volume_gain_db,
            )

            # Perform synthesis
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Save to file if requested
            if output_filename:
                with open(output_filename, "wb") as out:
                    out.write(response.audio_content)
                logger.info(f'Audio saved to "{output_filename}"')

            return response.audio_content

        except exceptions.GoogleAPIError as e:
            logger.error(f"Google API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise

    def synthesize_segment(
        self, segment: TextSegment, output_dir: Optional[str] = None
    ) -> bytes:
        """
        Synthesize a text segment with appropriate settings.

        Args:
            segment: TextSegment to synthesize
            output_dir: Output directory for temporary files

        Returns:
            Audio content as bytes
        """
        # Create filename based on segment info
        filename = None
        if output_dir:
            filename = os.path.join(
                output_dir,
                f"segment_ch{segment.chapter_number}_p{segment.paragraph_number}_s{segment.sentence_number}.mp3",
            )

        # Use SSML for better speech control
        from .text_processor import TextProcessor

        processor = TextProcessor()
        ssml_text = processor.create_ssml(segment.text)

        return self.synthesize_text(
            ssml_text,
            output_filename=filename,
            use_ssml=True,
            speaking_rate=Config.DEFAULT_SPEAKING_RATE,
            pitch=Config.DEFAULT_PITCH,
            volume_gain_db=Config.DEFAULT_VOLUME_GAIN_DB,
        )

    def batch_synthesize(
        self,
        segments: List[TextSegment],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> List[bytes]:
        """
        Synthesize multiple text segments in batch.

        Args:
            segments: List of TextSegment objects
            output_dir: Output directory for temporary files
            progress_callback: Callback function for progress updates

        Returns:
            List of audio content bytes
        """
        audio_segments = []

        for i, segment in enumerate(segments):
            try:
                audio_content = self.synthesize_segment(segment, output_dir)
                audio_segments.append(audio_content)

                if progress_callback:
                    progress_callback(i + 1, len(segments), segment)

            except Exception as e:
                logger.error(f"Failed to synthesize segment {i}: {e}")
                # Add silence as fallback
                audio_segments.append(b"")

        return audio_segments


# Legacy function for backward compatibility
def synthesize_text(
    text, output_filename="output.mp3", language_code="pt-BR", ssml_gender="FEMALE"
):
    """
    Legacy function for backward compatibility.

    Args:
        text (str): O texto a ser sintetizado.
        output_filename (str): O nome do arquivo de saída (ex: "audio.mp3").
        language_code (str): O código do idioma (ex: "en-US", "pt-BR").
        ssml_gender (str): Gênero da voz (MALE, FEMALE, NEUTRAL).
    """
    engine = TTSEngine(language_code, ssml_gender)
    return engine.synthesize_text(text, output_filename)


if __name__ == "__main__":
    # Example usage
    text_to_convert = "Olá! Este é um exemplo de texto convertido para voz usando o Google Text-to-Speech."

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # Generate audio using the new engine
    engine = TTSEngine("pt-BR", "FEMALE")
    output_file = f"output/meu_audio_ptbr_{int(time.time())}.mp3"

    try:
        engine.synthesize_text(text_to_convert, output_file)
        print(f"✓ Audio generated successfully: {output_file}")
    except Exception as e:
        print(f"✗ Error generating audio: {e}")

    # Example with English
    # engine_en = TTSEngine("en-US", "MALE")
    # engine_en.synthesize_text("Hello! This is an example of text converted to speech using Google Text-to-Speech.",
    #                          "output/my_audio_enus.mp3")
