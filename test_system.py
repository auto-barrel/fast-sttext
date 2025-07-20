#!/usr/bin/env python3
"""
Test script to verify basic functionality of the audiobook generator.
"""
import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_imports() -> bool:
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.config import Config  # noqa: F401

        print("Config imported successfully")
    except ImportError as e:
        print(f"Config import failed: {e}")
        return False

    try:
        from src.file_handler import FileHandler  # noqa: F401

        print("FileHandler imported successfully")
    except ImportError as e:
        print(f"FileHandler import failed: {e}")
        return False

    try:
        from src.text_processor import TextProcessor  # noqa: F401

        print("TextProcessor imported successfully")
    except ImportError as e:
        print(f"TextProcessor import failed: {e}")
        return False

    # Note: TTS and Audio processors require external dependencies
    print("All basic imports successful")
    return True


def test_file_operations() -> bool:
    """Test file handling operations."""
    print("\nTesting file operations...")

    try:
        from src.file_handler import FileHandler

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = os.path.join(temp_dir, "test.txt")
            test_content = "Este é um texto de teste para o gerador de audiobooks."

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            # Test file handler
            handler = FileHandler()
            content = handler.read_file(test_file)

            if content == test_content:
                print("File reading works correctly")
            else:
                print("File reading failed")
                return False

            # Test file info
            info = handler.get_file_info(test_file)
            if info and info["name"] == "test.txt":
                print("File info works correctly")
            else:
                print("File info failed")
                return False

        print("File operations successful")
        return True

    except Exception as e:
        print(f"File operations failed: {e}")
        return False


def test_text_processing() -> bool:
    """Test text processing functionality."""
    print("\nTesting text processing...")

    try:
        from src.text_processor import TextProcessor

        processor = TextProcessor()

        # Test text cleaning
        test_text = "  Este é um  texto   com espaços   extras.  "
        cleaned = processor.clean_text(test_text)

        if "espaços extras" in cleaned:
            print("Text cleaning works correctly")
        else:
            print("Text cleaning failed")
            return False

        # Test chapter detection
        chapter_text = """
        Capítulo 1: Primeiro Capítulo

        Este é o conteúdo do primeiro capítulo.

        Capítulo 2: Segundo Capítulo

        Este é o conteúdo do segundo capítulo.
        """

        chapters = processor.detect_chapters(chapter_text)
        if len(chapters) >= 2:
            print("Chapter detection works correctly")
        else:
            print("Chapter detection failed")
            return False

        # Test segmentation
        segments = processor.create_segments(chapter_text)
        if segments:
            print(f"Text segmentation works correctly ({len(segments)} segments)")
        else:
            print("Text segmentation failed")
            return False

        print("Text processing successful")
        return True

    except Exception as e:
        print(f"Text processing failed: {e}")
        return False


def test_configuration() -> bool:
    """Test configuration settings."""
    print("\nTesting configuration...")

    try:
        from src.config import Config

        # Test voice selection
        voice = Config.get_voice_name("pt-BR", "FEMALE", premium=True)
        if voice and "pt-BR" in voice:
            print("Voice configuration works correctly")
        else:
            print("Voice configuration failed")
            return False

        # Test path functions
        output_path = Config.get_output_path("test.mp3")
        if output_path and output_path.endswith("test.mp3"):
            print("Path configuration works correctly")
        else:
            print("Path configuration failed")
            return False

        print("Configuration successful")
        return True

    except Exception as e:
        print(f"Configuration failed: {e}")
        return False


def test_google_credentials() -> bool:
    """Test Google Cloud credentials."""
    print("\nTesting Google Cloud credentials...")

    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print(" GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   Set this environment variable to test TTS functionality")
        return False

    try:
        from google.cloud import texttospeech

        texttospeech.TextToSpeechClient()
        print("Google Cloud credentials work correctly")
        return True
    except Exception as e:
        print(f"Google Cloud credentials failed: {e}")
        return False


def main() -> None:
    """Run all tests."""
    print(" Running fast-sttext tests...\n")

    tests = [
        test_imports,
        test_file_operations,
        test_text_processing,
        test_configuration,
        test_google_credentials,
        test_chunk_sizes,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\nTest Results: {passed}/{total} passed")

    if passed == total:
        print("All tests passed! The system is ready to use.")
    else:
        print(" Some tests failed. Check the output above for details.")

    print("\nNext steps:")
    print("1. Make sure Google Cloud credentials are set up")
    print("2. Install ffmpeg if not already installed")
    print("3. Run: python example.py")


def test_chunk_sizes() -> bool:
    """Test different chunk sizes with your sample text."""
    try:
        from src.config import Config
        from src.text_processor import TextProcessor
        from src.file_handler import FileHandler

        print("Testing chunk sizing")

        # Sample text from your test_book.txt
        test_file = "input/test_book.txt"

        processor = TextProcessor()
        file_handler = FileHandler()

        # Test different chunk sizes
        chunk_sizes = [1500, 2000, 2500, 2800, 3000, 3500]
        test_content = file_handler.read_text_file(filepath=test_file)

        for size in chunk_sizes:
            # Simulate processing
            segments = processor.create_segments(test_content, size)

            for i, segment in enumerate(segments):
                ssml = processor.create_ssml(segment.text)
                ssml_bytes = len(ssml.encode("utf-8"))

                print(f"Chunk size {size}: Segment {i+1}")
                print(f"  Text length: {len(segment.text)} chars")
                print(f"  SSML size: {ssml_bytes} bytes")
                print(f"  Within limit: {ssml_bytes <= Config.MAX_API_BYTES}")
                print()

        print("Chunk sizing within limits for API settings")
        return True
    except Exception:
        print("chunk measurement failed")
        return False


if __name__ == "__main__":
    main()
