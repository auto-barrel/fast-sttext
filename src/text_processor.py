"""
Text processing module for audiobook generation.
Handles text segmentation, cleaning, and SSML generation.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import nltk
from nltk.tokenize import sent_tokenize, PunktSentenceTokenizer


@dataclass
class TextSegment:
    """Represents a segment of text with metadata."""

    text: str
    segment_type: str  # 'sentence', 'paragraph', 'chapter'
    chapter_number: int = 0
    paragraph_number: int = 0
    sentence_number: int = 0


class TextProcessor:
    """Handles text processing and segmentation for audiobook generation."""

    def __init__(self, language: str = "portuguese"):
        """Initialize text processor with language-specific settings."""
        self.language = language

        # Download required NLTK data
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

        # Initialize the sentence tokenizer
        self.sentence_tokenizer = PunktSentenceTokenizer()

    def clean_text(self, text: str) -> str:
        """Clean and normalize text for TTS processing."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Fix common punctuation issues
        text = re.sub(r"([.!?])\s*([.!?])", r"\1 \2", text)

        # Add proper spacing after punctuation
        text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)

        # Handle abbreviations common in Portuguese
        abbreviations = {
            "dr.": "doutor",
            "dra.": "doutora",
            "sr.": "senhor",
            "sra.": "senhora",
            "prof.": "professor",
            "profa.": "professora",
            "etc.": "et cetera",
            "ex.": "exemplo",
            "obs.": "observação",
        }

        for abbr, full in abbreviations.items():
            text = re.sub(re.escape(abbr), full, text, flags=re.IGNORECASE)

        # Handle numbers
        text = re.sub(r"\b(\d+)\b", r'<say-as interpret-as="number">\1</say-as>', text)

        return text.strip()

    def detect_chapters(self, text: str) -> List[Tuple[int, str]]:
        """Detect chapter boundaries in text."""
        chapters = []
        chapter_patterns = [
            r"^\s*capítulo\s+(\d+|[ivx]+)\s*:?\s*(.*)$",
            r"^\s*chapter\s+(\d+|[ivx]+)\s*:?\s*(.*)$",
            r"^\s*(\d+)\.\s*(.*)$",
            r"^\s*parte\s+(\d+|[ivx]+)\s*:?\s*(.*)$",
        ]

        lines = text.split("\n")
        current_chapter = 1
        current_text = ""

        for line in lines:
            line = line.strip()
            if not line:
                current_text += "\n"
                continue

            is_chapter = False
            for pattern in chapter_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous chapter if exists
                    if current_text.strip():
                        chapters.append((current_chapter, current_text.strip()))

                    # Start new chapter
                    current_chapter += 1
                    current_text = ""
                    is_chapter = True
                    break

            if not is_chapter:
                current_text += line + "\n"

        # Add the last chapter
        if current_text.strip():
            chapters.append((current_chapter, current_text.strip()))

        # If no chapters detected, treat entire text as one chapter
        if not chapters:
            chapters = [(1, text)]

        return chapters

    def split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = []
        current_paragraph = ""

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
            else:
                current_paragraph += " " + line if current_paragraph else line

        if current_paragraph:
            paragraphs.append(current_paragraph.strip())

        return [p for p in paragraphs if p]

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK."""
        try:
            # Use the tokenizer's tokenize method
            sentences = self.sentence_tokenizer.tokenize(text)
            return [s.strip() for s in sentences if s.strip()]
        except Exception as e:
            # Fallback to basic sentence splitting if NLTK fails
            print(f"NLTK tokenization failed: {e}, falling back to basic splitting")
            return self._basic_sentence_split(text)

    def _basic_sentence_split(self, text: str) -> List[str]:
        """Fallback sentence splitting method."""
        # Simple sentence splitting on common sentence endings
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def create_segments(self, text: str, max_length: int = 4000) -> List[TextSegment]:
        """Create text segments suitable for TTS processing."""
        segments = []
        chapters = self.detect_chapters(text)

        for chapter_num, chapter_text in chapters:
            paragraphs = self.split_into_paragraphs(chapter_text)

            for para_num, paragraph in enumerate(paragraphs, 1):
                sentences = self.split_into_sentences(paragraph)

                # Group sentences into chunks that fit within max_length
                current_chunk = ""
                chunk_sentences = []

                for sent_num, sentence in enumerate(sentences, 1):
                    cleaned_sentence = self.clean_text(sentence)

                    # Check if adding this sentence would exceed max_length
                    if (
                        len(current_chunk) + len(cleaned_sentence) + 1 > max_length
                        and current_chunk
                    ):
                        # Save current chunk
                        segments.append(
                            TextSegment(
                                text=current_chunk.strip(),
                                segment_type="paragraph",
                                chapter_number=chapter_num,
                                paragraph_number=para_num,
                                sentence_number=len(chunk_sentences),
                            )
                        )

                        # Start new chunk
                        current_chunk = cleaned_sentence
                        chunk_sentences = [sentence]
                    else:
                        current_chunk += (
                            " " + cleaned_sentence
                            if current_chunk
                            else cleaned_sentence
                        )
                        chunk_sentences.append(sentence)

                # Add the last chunk
                if current_chunk:
                    segments.append(
                        TextSegment(
                            text=current_chunk.strip(),
                            segment_type="paragraph",
                            chapter_number=chapter_num,
                            paragraph_number=para_num,
                            sentence_number=len(chunk_sentences),
                        )
                    )

        return segments

    def create_ssml(self, text: str, add_pauses: bool = True) -> str:
        """Create SSML markup for better speech synthesis."""
        # Wrap in SSML speak tags
        ssml = f"<speak>{text}</speak>"

        if add_pauses:
            # Add pauses after sentences
            ssml = re.sub(r"([.!?])\s+", r'\1 <break time="0.8s"/> ', ssml)

            # Add longer pauses for paragraph breaks
            ssml = re.sub(r"\n\s*\n", '<break time="1.5s"/>', ssml)

        return ssml

    def get_segment_info(self, segment: TextSegment) -> Dict:
        """Get metadata information for a segment."""
        return {
            "chapter": segment.chapter_number,
            "paragraph": segment.paragraph_number,
            "sentence": segment.sentence_number,
            "type": segment.segment_type,
            "length": len(segment.text),
            "word_count": len(segment.text.split()),
        }
