#!/usr/bin/env python3
"""
Main application for fast-sttext audiobook generator.
Converts text files to audiobooks using Google Text-to-Speech API.
"""
import logging
import os
import sys
from typing import List, Optional

import click
from colorama import Fore, Style, init
from tqdm import tqdm

from audio_processor import AudioProcessor

# Import our modules
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

        # Read input file
        print(f"{Fore.BLUE}📖 Reading input file...{Style.RESET_ALL}")
        try:
            text_content = self.file_handler.read_file(input_file)
            print(f"{Fore.GREEN}✓ Successfully read {len(text_content)} characters{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to read file: {e}{Style.RESET_ALL}")
            return []

        # Process text into segments
        print(f"{Fore.BLUE}Processing text...{Style.RESET_ALL}")
        try:
            segments = self.text_processor.create_segments(text_content, Config.CHUNK_SIZE)

            if preview_mode:
                segments = segments[:5]  # Only first 5 segments for preview
                print(f"{Fore.YELLOW}Preview mode: Using only first 5 segments{Style.RESET_ALL}")

            print(f"{Fore.GREEN}✓ Created {len(segments)} text segments{Style.RESET_ALL}")

            # Show chapter information
            chapters = {}
            for segment in segments:
                chapter_num = segment.chapter_number
                if chapter_num not in chapters:
                    chapters[chapter_num] = 0
                chapters[chapter_num] += 1

            print(f"{Fore.CYAN}📚 Found {len(chapters)} chapters{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}✗ Failed to process text: {e}{Style.RESET_ALL}")
            return []

        # Generate audio segments
        print(f"{Fore.BLUE}🎤 Generating audio segments...{Style.RESET_ALL}")
        audio_bytes_list = []
        segments_info = []

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
                for segment in segments:
                    segments_info.append(self.text_processor.get_segment_info(segment))

                print(f"{Fore.GREEN}✓ Generated {len(audio_bytes_list)} audio segments{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}✗ Failed to generate audio: {e}{Style.RESET_ALL}")
                return []

        # Create output filename
        if not output_name:
            output_name = self.file_handler.create_output_filename(input_file, "preview" if preview_mode else "")

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

                # Add metadata
                metadata = {
                    "title": os.path.basename(input_file),
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

                return output_files
            else:
                print(f"{Fore.RED}✗ Failed to create audiobook{Style.RESET_ALL}")
                return []

        except Exception as e:
            print(f"{Fore.RED}✗ Failed to create audiobook: {e}{Style.RESET_ALL}")
            return []

    def list_available_voices(self) -> None:
        """List available voices for current language."""
        print(f"{Fore.BLUE}🎭 Available voices for {self.language}:{Style.RESET_ALL}")

        voices = self.tts_engine.list_available_voices()
        if voices:
            for voice in voices:
                voice_type = "Premium" if "Wavenet" in voice["name"] else "Standard"
                print(f"  • {voice['name']} ({voice['gender']}) - {voice_type}")
        else:
            print(f"{Fore.YELLOW}No voices found{Style.RESET_ALL}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.audio_processor.cleanup()


# CLI Interface
@click.group()
def cli() -> None:
    """Fast-STText: Convert text files to audiobooks using Google Text-to-Speech."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output filename")
@click.option("--language", "-l", default="pt-BR", help="Language code (default: pt-BR)")
@click.option(
    "--voice",
    "-v",
    default="FEMALE",
    type=click.Choice(["MALE", "FEMALE", "NEUTRAL"]),
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
    input_file: str, output: str, language: str, voice: str, premium: bool, chapters: bool, preview: bool
) -> None:
    """Generate audiobook from input file."""

    # Check for Google Cloud credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print(f"{Fore.RED}GOOGLE_APPLICATION_CREDENTIALS environment variable not set{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please set up Google Cloud credentials first{Style.RESET_ALL}")
        sys.exit(1)

    generator = None
    try:
        generator = AudiobookGenerator(language, voice, premium)

        output_files = generator.generate_audiobook(input_file, output, chapters, preview)

        if output_files:
            print(f"\n{Fore.GREEN}Audiobook generation completed!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Generated files:{Style.RESET_ALL}")
            for file in output_files:
                if file:
                    print(f"  {file}")
        else:
            print(f"\n{Fore.RED}Audiobook generation failed{Style.RESET_ALL}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Generation interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        if generator:
            generator.cleanup()


@cli.command()
@click.option("--language", "-l", default="pt-BR", help="Language code (default: pt-BR)")
def voices(language: str) -> None:
    """List available voices for specified language."""
    try:
        generator = AudiobookGenerator(language)
        generator.list_available_voices()
    except Exception as e:
        print(f"{Fore.RED}Error listing voices: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
def files() -> None:
    """List available input files."""
    try:
        file_handler = FileHandler()
        input_files = file_handler.list_input_files()

        if input_files:
            print(f"{Fore.BLUE}Available input files:{Style.RESET_ALL}")
            for file in input_files:
                file_info = file_handler.get_file_info(file)
                print(f"  • {file_info['name']} ({file_info['size_formatted']})")
        else:
            print(f"{Fore.YELLOW}No input files found in {Config.INPUT_DIR}{Style.RESET_ALL}")
            supported_formats = ", ".join(Config.SUPPORTED_TEXT_FORMATS + Config.SUPPORTED_EBOOK_FORMATS)
            print(f"{Fore.CYAN}Supported formats: {supported_formats} {Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error listing files: {e}{Style.RESET_ALL}")
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
        sys.exit(1)


if __name__ == "__main__":
    cli()
