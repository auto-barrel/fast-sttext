"""
File handling module for audiobook generation.
Handles reading various file formats and preparing text for processing.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Config

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations for audiobook generation."""

    def __init__(self) -> None:
        """Initialize file handler."""
        self.input_dir = Config.INPUT_DIR
        self.output_dir = Config.OUTPUT_DIR

        # Create directories if they don't exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def list_input_files(self) -> List[str]:
        """List all supported files in input directory."""
        supported_extensions = Config.SUPPORTED_TEXT_FORMATS + Config.SUPPORTED_EBOOK_FORMATS

        files: List[Path] = []
        for ext in supported_extensions:
            pattern = f"*{ext}"
            files.extend(Path(self.input_dir).glob(pattern))

        return [str(f) for f in files]

    def read_text_file(self, filepath: str) -> str:
        """
        Read a text file and return its content.

        Args:
            filepath: Path to the text file

        Returns:
            File content as string
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Read text file: {filepath} ({len(content)} characters)")
            return content

        except UnicodeDecodeError:
            # Try different encodings
            encodings = ["latin-1", "iso-8859-1", "cp1252"]
            for encoding in encodings:
                try:
                    with open(filepath, "r", encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"Read text file with {encoding} encoding: {filepath}")
                    return content
                except UnicodeDecodeError:
                    continue

            logger.error(f"Failed to read file with any encoding: {filepath}")
            raise

        except Exception as e:
            logger.error(f"Failed to read text file {filepath}: {e}")
            raise

    def read_pdf_file(self, filepath: str) -> str:
        """
        Read a PDF file and extract text content.

        Args:
            filepath: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            import PyPDF2

            text = ""
            with open(filepath, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"

            logger.info(f"Extracted text from PDF: {filepath} ({len(text)} characters)")
            return text

        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            raise
        except Exception as e:
            logger.error(f"Failed to read PDF file {filepath}: {e}")
            raise

    def read_epub_file(self, filepath: str) -> str:
        """
        Read an EPUB file and extract text content.

        Args:
            filepath: Path to the EPUB file

        Returns:
            Extracted text content
        """
        try:
            import ebooklib  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore
            from ebooklib import epub

            book = epub.read_epub(filepath)
            text = ""

            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    text += soup.get_text() + "\n"

            logger.info(f"Extracted text from EPUB: {filepath} ({len(text)} characters)")
            return text

        except ImportError:
            logger.error("ebooklib and beautifulsoup4 not installed. Install with: pip install ebooklib beautifulsoup4")
            raise
        except Exception as e:
            logger.error(f"Failed to read EPUB file {filepath}: {e}")
            raise

    def read_file(self, filepath: str) -> str:
        """
        Read any supported file format and return text content.

        Args:
            filepath: Path to the file

        Returns:
            Text content of the file
        """
        file_path = Path(filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension in Config.SUPPORTED_TEXT_FORMATS:
            return self.read_text_file(str(file_path))
        elif extension == ".pdf":
            return self.read_pdf_file(str(file_path))
        elif extension == ".epub":
            return self.read_epub_file(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get information about a file.

        Args:
            filepath: Path to the file

        Returns:
            Dictionary with file information
        """
        try:
            path = Path(filepath)
            stat = path.stat()

            return {
                "name": path.name,
                "size": stat.st_size,
                "size_formatted": self.format_file_size(stat.st_size),
                "modified": stat.st_mtime,
                "extension": path.suffix.lower(),
                "is_supported": path.suffix.lower() in (Config.SUPPORTED_TEXT_FORMATS + Config.SUPPORTED_EBOOK_FORMATS),
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {filepath}: {e}")
            return {}

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in bytes to human readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size_float = float(size_bytes)

        while size_float >= 1024 and i < len(size_names) - 1:
            size_float /= 1024.0
            i += 1

        return f"{size_float:.1f} {size_names[i]}"

    def create_output_filename(self, input_filename: str, suffix: str = "") -> str:
        """
        Create an output filename based on input filename.

        Args:
            input_filename: Original filename
            suffix: Optional suffix to add

        Returns:
            Output filename
        """
        input_path = Path(input_filename)
        base_name = input_path.stem

        if suffix:
            output_name = f"{base_name}_{suffix}.mp3"
        else:
            output_name = f"{base_name}.mp3"

        return output_name

    def cleanup_output_directory(self, pattern: str = "*.mp3") -> None:
        """
        Clean up files in output directory matching pattern.

        Args:
            pattern: File pattern to match
        """
        try:
            output_path = Path(self.output_dir)
            files = list(output_path.glob(pattern))

            for file in files:
                file.unlink()
                logger.info(f"Deleted: {file}")

            logger.info(f"Cleaned up {len(files)} files from output directory")
        except Exception as e:
            logger.error(f"Failed to cleanup output directory: {e}")

    def get_input_file_by_name(self, filename: str) -> Optional[str]:
        """
        Get full path of input file by name.

        Args:
            filename: Name of the file

        Returns:
            Full path if found, None otherwise
        """
        input_path = Path(self.input_dir) / filename

        if input_path.exists():
            return str(input_path)

        # Try to find file with similar name
        for file in self.list_input_files():
            if Path(file).name.lower() == filename.lower():
                return file

        return None
