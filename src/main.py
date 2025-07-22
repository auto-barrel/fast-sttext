#!/usr/bin/env python3
"""
Main application for fast-sttext audiobook generator.
Converts text files to audiobooks using Google Text-to-Speech API.
"""
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import click
from colorama import Fore, Style, init
from tqdm import tqdm

from audio_processor import AudioProcessor
from config import Config
from file_handler import FileHandler
from text_processor import TextProcessor, TextSegment
from tts_engine import TTSEngine

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("audiobook_generator.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AudiobookGenerator:
    """Main class for audiobook generation."""

    def __init__(
        self,
        language: str = "pt-BR",
        voice_gender: str = "FEMALE",
        premium_voices: bool = True,
    ):
        """
        Initialize audiobook generator.

        Args:
            language: Language code (e.g., "pt-BR", "en-US")
            voice_gender: Voice gender (MALE, FEMALE, NEUTRAL)
            premium_voices: Whether to use premium Wavenet voices
        """
        self.language = language
        self.voice_gender = voice_gender
        self.premium_voices = premium_voices

        # Initialize components
        self.file_handler = FileHandler()
        self.text_processor = TextProcessor()
        self.tts_engine = TTSEngine(language, voice_gender, premium_voices)
        self.audio_processor = AudioProcessor()

        logger.info(f"Audiobook generator initialized with language: {language}, voice: {voice_gender}")

    def generate_audiobook(
        self,
        input_file: str,
        output_name: Optional[str] = None,
        split_chapters: bool = False,
        preview_mode: bool = False,
    ) -> List[str]:
        """
        Generate audiobook from input file.

        Args:
            input_file: Path to input file
            output_name: Custom output filename
            split_chapters: Whether to create separate files for chapters
            preview_mode: Generate only first few segments for preview

        Returns:
            List of generated audio file paths
        """
        logger.info(f"Starting audiobook generation for: {input_file}")

        # Validate and read input
        text_content = self._read_and_validate_input(input_file)
        if not text_content:
            return []

        # Process text into segments
        segments = self._process_text_to_segments(text_content, preview_mode)
        if not segments:
            return []

        # Generate audio from segments
        audio_data = self._generate_audio_segments(segments)
        if not audio_data:
            return []

        # Create final audiobook files
        return self._create_audiobook_files(audio_data, input_file, output_name, split_chapters, preview_mode)

    def _read_and_validate_input(self, input_file: str) -> str:
        """Read and validate input file."""
        # Validate input file exists and is readable
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not input_path.is_file():
            raise ValueError(f"Input path is not a file: {input_file}")

        # Read input file
        print(f"{Fore.BLUE}📖 Reading input file...{Style.RESET_ALL}")
        try:
            text_content = self.file_handler.read_file(input_file)
            print(f"{Fore.GREEN}✓ Successfully read {len(text_content)} characters{Style.RESET_ALL}")

            # Validate content
            if not text_content.strip():
                print(f"{Fore.RED}✗ Input file is empty or contains no readable text{Style.RESET_ALL}")
                return ""

            return text_content

        except Exception as e:
            print(f"{Fore.RED}✗ Failed to read file: {e}{Style.RESET_ALL}")
            return ""

    def _process_text_to_segments(self, text_content: str, preview_mode: bool) -> List[TextSegment]:
        """Process text into segments for TTS."""
        print(f"{Fore.BLUE}🔧 Processing text...{Style.RESET_ALL}")
        try:
            segments = self.text_processor.create_segments(text_content, Config.CHUNK_SIZE)

            if preview_mode:
                segments = segments[:5]  # Only first 5 segments for preview
                print(f"{Fore.YELLOW}Preview mode: Using only first 5 segments{Style.RESET_ALL}")

            print(f"{Fore.GREEN}✓ Created {len(segments)} text segments{Style.RESET_ALL}")

            # Show chapter information
            self._display_chapter_info(segments)

            return segments

        except Exception as e:
            print(f"{Fore.RED}✗ Failed to process text: {e}{Style.RESET_ALL}")
            return []

    def _display_chapter_info(self, segments: List[TextSegment]) -> None:
        """Display chapter information from segments."""
        chapters = {}
        for segment in segments:
            chapter_num = segment.chapter_number
            if chapter_num not in chapters:
                chapters[chapter_num] = 0
            chapters[chapter_num] += 1

        print(f"{Fore.CYAN}📚 Found {len(chapters)} chapters{Style.RESET_ALL}")

    def _generate_audio_segments(self, segments: List[TextSegment]) -> Optional[tuple]:
        """Generate audio from text segments."""
        print(f"{Fore.BLUE}🎤 Generating audio segments...{Style.RESET_ALL}")

        with tqdm(total=len(segments), desc="Synthesizing", unit="segments") as pbar:

            def progress_callback(current: int, total: int, segment: TextSegment) -> None:
                pbar.set_postfix(
                    {
                        "chapter": segment.chapter_number,
                        "paragraph": segment.paragraph_number,
                    }
                )
                pbar.update(1)

            try:
                audio_bytes_list = self.tts_engine.batch_synthesize(segments, progress_callback=progress_callback)

                # Create segments info for audio processing
                segments_info = []
                for segment in segments:
                    segments_info.append(self.text_processor.get_segment_info(segment))

                print(f"{Fore.GREEN}✓ Generated {len(audio_bytes_list)} audio segments{Style.RESET_ALL}")
                return (audio_bytes_list, segments_info)

            except Exception as e:
                print(f"{Fore.RED}✗ Failed to generate audio: {e}{Style.RESET_ALL}")
                return None

    def _create_audiobook_files(
        self,
        audio_data: tuple,
        input_file: str,
        output_name: Optional[str],
        split_chapters: bool,
        preview_mode: bool,
    ) -> List[str]:
        """Create final audiobook files from audio data."""
        audio_bytes_list, segments_info = audio_data
        input_path = Path(input_file)

        # Create output filename
        if not output_name:
            output_name = self.file_handler.create_output_filename(input_file, "preview" if preview_mode else "")

        # Validate output filename
        if not output_name.endswith(".mp3"):
            output_name += ".mp3"

        # Generate final audiobook
        print(f"{Fore.BLUE}🎵 Creating audiobook...{Style.RESET_ALL}")
        try:
            if split_chapters:
                output_files = self.audio_processor.create_chapter_files(
                    audio_bytes_list, segments_info, output_name.replace(".mp3", "")
                )
            else:
                output_file = self.audio_processor.create_audiobook_from_bytes(
                    audio_bytes_list, segments_info, output_name
                )
                output_files = [output_file] if output_file else []

            if output_files:
                print(f"{Fore.GREEN}✓ Successfully created audiobook(s){Style.RESET_ALL}")
                self._add_metadata_and_display_info(output_files, input_path)
                return output_files
            else:
                print(f"{Fore.RED}✗ Failed to create audiobook{Style.RESET_ALL}")
                return []

        except Exception as e:
            print(f"{Fore.RED}✗ Failed to create audiobook: {e}{Style.RESET_ALL}")
            return []

    def _add_metadata_and_display_info(self, output_files: List[str], input_path: Path) -> None:
        """Add metadata to output files and display file information."""
        metadata = {
            "title": input_path.stem,
            "artist": "AI Narrator",
            "album": "Audiobook",
            "genre": "Audiobook",
            "language": self.language,
        }

        for output_file in output_files:
            if output_file:
                self.audio_processor.add_metadata(output_file, metadata)

                # Show file info
                audio_info = self.audio_processor.get_audio_info(output_file)
                print(
                    f"{Fore.CYAN}{os.path.basename(output_file)}: "
                    f"{audio_info.get('duration_formatted', 'Unknown')} duration"
                    f"{Style.RESET_ALL}"
                )

    def list_available_voices(self) -> None:
        """List available voices for current language."""
        print(f"{Fore.BLUE}Available voices for {self.language}:{Style.RESET_ALL}")

        try:
            voices = self.tts_engine.list_available_voices()
            if voices:
                for voice in voices:
                    voice_type = "Premium" if "Wavenet" in voice["name"] else "Standard"
                    print(f"  • {voice['name']} ({voice['gender']}) - {voice_type}")
            else:
                print(f"{Fore.YELLOW}No voices found for language: {self.language}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error retrieving voices: {e}{Style.RESET_ALL}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.audio_processor.cleanup()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


def validate_credentials() -> bool:
    """Validate Google Cloud credentials."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not creds_path:
        print(f"{Fore.RED}✗ GOOGLE_APPLICATION_CREDENTIALS environment variable not set{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please set up Google Cloud credentials first{Style.RESET_ALL}")
        print(
            (
                f"{Fore.CYAN}Example: export GOOGLE_APPLICATION_CREDENTIALS="
                f"'/path/to/service-account-key.json'{Style.RESET_ALL}"
            )
        )
        return False

    if not os.path.exists(creds_path):
        print(f"{Fore.RED}✗ Credentials file not found: {creds_path}{Style.RESET_ALL}")
        return False

    try:
        # Try to initialize a client to validate credentials
        from google.cloud import texttospeech

        texttospeech.TextToSpeechClient()
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Invalid Google Cloud credentials: {e}{Style.RESET_ALL}")
        return False


def validate_language_code(language: str) -> bool:
    """Validate language code format."""
    import re

    # Basic validation for language codes like 'pt-BR', 'en-US', etc.
    pattern = r"^[a-z]{2}(-[A-Z]{2})?$"
    if not re.match(pattern, language):
        print(f"{Fore.RED}✗ Invalid language code format: {language}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Expected format: 'pt-BR', 'en-US', 'fr-FR', etc.{Style.RESET_ALL}")
        return False
    return True


# CLI Interface
@click.group()
@click.version_option(version="0.1.0", prog_name="fast-sttext")
def cli() -> None:
    """Fast-STText: Convert text files to audiobooks using Google Text-to-Speech."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option("--output", "-o", type=str, help="Output filename (with or without .mp3 extension)")
@click.option("--language", "-l", default="pt-BR", help="Language code (default: pt-BR)")
@click.option(
    "--voice",
    "-v",
    default="FEMALE",
    type=click.Choice(["MALE", "FEMALE", "NEUTRAL"], case_sensitive=False),
    help="Voice gender (default: FEMALE)",
)
@click.option(
    "--premium/--no-premium",
    default=True,
    help="Use premium Wavenet voices (default: True)",
)
@click.option("--chapters/--no-chapters", default=False, help="Split output into chapter files")
@click.option("--preview", is_flag=True, help="Generate preview with first 5 segments only")
def generate(
    input_file: str, output: Optional[str], language: str, voice: str, premium: bool, chapters: bool, preview: bool
) -> None:
    """Generate audiobook from input file."""

    # Validate inputs
    if not validate_credentials():
        sys.exit(1)

    if not validate_language_code(language):
        sys.exit(1)

    # Normalize voice parameter
    voice = voice.upper()

    generator = None
    try:
        print(f"{Fore.BLUE}🚀 Starting audiobook generation...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Input: {input_file}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Language: {language}, Voice: {voice}, Premium: {premium}{Style.RESET_ALL}")

        generator = AudiobookGenerator(language, voice, premium)

        output_files = generator.generate_audiobook(input_file, output, chapters, preview)

        if output_files:
            print(f"\n{Fore.GREEN}🎉 Audiobook generation completed!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Generated files:{Style.RESET_ALL}")
            for file in output_files:
                if file:
                    full_path = os.path.abspath(file)
                    print(f"  📁 {full_path}")
        else:
            print(f"\n{Fore.RED}✗ Audiobook generation failed{Style.RESET_ALL}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Generation interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}💥 Error: {e}{Style.RESET_ALL}")
        logger.exception("Audiobook generation failed")
        sys.exit(1)
    finally:
        if generator:
            generator.cleanup()


@cli.command()
@click.option("--language", "-l", default="pt-BR", help="Language code (default: pt-BR)")
def voices(language: str) -> None:
    """List available voices for specified language."""
    if not validate_credentials():
        sys.exit(1)

    if not validate_language_code(language):
        sys.exit(1)

    generator = None
    try:
        generator = AudiobookGenerator(language)
        generator.list_available_voices()
    except Exception as e:
        print(f"{Fore.RED}Error listing voices: {e}{Style.RESET_ALL}")
        logger.exception("Failed to list voices")
        sys.exit(1)
    finally:
        if generator:
            generator.cleanup()


@cli.command()
def files() -> None:
    """List available input files."""
    try:
        file_handler = FileHandler()
        input_files = file_handler.list_input_files()

        if input_files:
            print(f"{Fore.BLUE}📁 Available input files:{Style.RESET_ALL}")
            for file in input_files:
                file_info = file_handler.get_file_info(file)
                status = "✓" if file_info.get("is_supported", False) else "✗"
                print(f"  {status} {file_info['name']} ({file_info['size_formatted']})")
        else:
            print(f"{Fore.YELLOW}📂 No input files found in {Config.INPUT_DIR}{Style.RESET_ALL}")
            supported_formats = ", ".join(Config.SUPPORTED_TEXT_FORMATS + Config.SUPPORTED_EBOOK_FORMATS)
            print(f"{Fore.CYAN}Supported formats: {supported_formats}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error listing files: {e}{Style.RESET_ALL}")
        logger.exception("Failed to list files")
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to clean up all output files?")
def cleanup() -> None:
    """Clean up all generated audio files."""
    try:
        file_handler = FileHandler()
        file_handler.cleanup_output_directory()
        print(f"{Fore.GREEN}✓ Output directory cleaned up{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error cleaning up: {e}{Style.RESET_ALL}")
        logger.exception("Failed to cleanup")
        sys.exit(1)


@cli.command()
def config() -> None:
    """Show current configuration."""
    print(f"{Fore.BLUE}⚙️  Current Configuration:{Style.RESET_ALL}")
    print(f"  Input Directory: {Config.INPUT_DIR}")
    print(f"  Output Directory: {Config.OUTPUT_DIR}")
    print(f"  Default Language: {Config.DEFAULT_LANGUAGE_CODE}")
    print(f"  Default Voice Gender: {Config.DEFAULT_VOICE_GENDER}")
    print(f"  Chunk Size: {Config.CHUNK_SIZE}")
    print(f"  Max API Bytes: {Config.MAX_API_BYTES}")

    # Check credentials
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"  Google Credentials: {creds_path}")
        if os.path.exists(creds_path):
            print(f"  {Fore.GREEN}✓ Credentials file exists{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Credentials file not found{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}✗ GOOGLE_APPLICATION_CREDENTIALS not set{Style.RESET_ALL}")


if __name__ == "__main__":
    cli()
