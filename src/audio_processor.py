"""
Audio processing module for audiobook generation.
Handles audio manipulation, concatenation, and format conversion.
"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from pydub import AudioSegment  # type: ignore

from config import Config

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio processing and manipulation for audiobook generation."""

    def __init__(self) -> None:
        """Initialize audio processor."""
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Audio processor initialized with temp dir: {self.temp_dir}")

    def bytes_to_audio_segment(self, audio_bytes: bytes) -> AudioSegment:
        """Convert audio bytes to AudioSegment."""
        # Save bytes to temporary file
        temp_file = os.path.join(self.temp_dir, f"temp_{os.getpid()}.mp3")
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        # Load as AudioSegment
        audio = AudioSegment.from_mp3(temp_file)

        # Clean up
        os.remove(temp_file)

        return audio

    def add_silence(self, duration_ms: int) -> AudioSegment:
        """Create silence of specified duration."""
        return AudioSegment.silent(duration=duration_ms)

    def normalize_audio(self, audio: AudioSegment, target_dBFS: float = -20.0) -> AudioSegment:
        """Normalize audio to target dBFS level."""
        change_in_dBFS = target_dBFS - audio.dBFS
        return audio.apply_gain(change_in_dBFS)

    def add_fade(self, audio: AudioSegment, fade_in_ms: int = 500, fade_out_ms: int = 500) -> AudioSegment:
        """Add fade in/out to audio."""
        return audio.fade_in(fade_in_ms).fade_out(fade_out_ms)

    def concatenate_audio_segments(self, audio_segments: List[AudioSegment], add_pauses: bool = True) -> AudioSegment:
        """
        Concatenate multiple audio segments with optional pauses.

        Args:
            audio_segments: List of AudioSegment objects
            add_pauses: Whether to add pauses between segments

        Returns:
            Concatenated AudioSegment
        """
        if not audio_segments:
            return AudioSegment.silent(duration=1000)

        result = audio_segments[0]

        for i in range(1, len(audio_segments)):
            if add_pauses:
                pause_duration = Config.PAUSE_BETWEEN_SENTENCES
                result += self.add_silence(pause_duration)

            result += audio_segments[i]

        return result

    def create_audiobook_from_bytes(
        self,
        audio_bytes_list: List[bytes],
        segments_info: Optional[List[Dict]] = None,
        output_filename: str = "audiobook.mp3",
    ) -> Optional[str]:
        """
        Create an audiobook from a list of audio bytes.

        Args:
            audio_bytes_list: List of audio content as bytes
            segments_info: Optional metadata for segments
            output_filename: Output filename

        Returns:
            Path to the generated audiobook
        """
        logger.info(f"Creating audiobook from {len(audio_bytes_list)} segments")

        # Convert bytes to AudioSegments
        audio_segments = []
        for i, audio_bytes in enumerate(audio_bytes_list):
            if audio_bytes:  # Skip empty bytes
                try:
                    segment = self.bytes_to_audio_segment(audio_bytes)
                    segment = self.normalize_audio(segment)
                    audio_segments.append(segment)
                except Exception as e:
                    logger.warning(f"Failed to process audio segment {i}: {e}")

        if not audio_segments:
            logger.error("No valid audio segments found")
            return None

        # Add chapter breaks if segment info is provided
        final_segments = []
        current_chapter = None

        for i, segment in enumerate(audio_segments):
            if segments_info and i < len(segments_info):
                segment_info = segments_info[i]
                chapter_num = segment_info.get("chapter", 1)

                # Add chapter break if new chapter
                if current_chapter is not None and chapter_num != current_chapter:
                    final_segments.append(self.add_silence(Config.PAUSE_BETWEEN_CHAPTERS))
                    logger.info(f"Added chapter break before chapter {chapter_num}")

                current_chapter = chapter_num

            final_segments.append(segment)

        # Concatenate all segments
        audiobook = self.concatenate_audio_segments(final_segments, add_pauses=True)

        # Add fade in/out
        audiobook = self.add_fade(audiobook, fade_in_ms=1000, fade_out_ms=2000)

        # Export to file
        output_path = Config.get_output_path(output_filename)
        audiobook.export(output_path, format="mp3", bitrate="128k")

        logger.info(f"Audiobook created: {output_path}")
        logger.info(f"Duration: {len(audiobook) / 1000:.1f} seconds")

        return output_path

    def create_chapter_files(
        self,
        audio_bytes_list: List[bytes],
        segments_info: Optional[List[Dict]] = None,
        output_prefix: str = "chapter",
    ) -> List[str]:
        """
        Create separate audio files for each chapter.

        Args:
            audio_bytes_list: List of audio content as bytes
            segments_info: Metadata for segments
            output_prefix: Prefix for output files

        Returns:
            List of paths to generated chapter files
        """
        if not segments_info:
            logger.warning("No segment info provided, creating single file")
            result = self.create_audiobook_from_bytes(audio_bytes_list, segments_info)
            return [result] if result else []

        # Group segments by chapter
        chapters: dict[int, list[tuple[int, dict]]] = {}
        for i, segment_info in enumerate(segments_info):
            if i < len(audio_bytes_list):
                chapter_num = segment_info.get("chapter", 1)
                if chapter_num not in chapters:
                    chapters[chapter_num] = []
                chapters[chapter_num].append((i, segment_info))

        # Create audio file for each chapter
        chapter_files = []
        for chapter_num in sorted(chapters.keys()):
            chapter_segments = chapters[chapter_num]
            chapter_audio_bytes = [audio_bytes_list[i] for i, _ in chapter_segments]
            chapter_info = [info for _, info in chapter_segments]

            filename = f"{output_prefix}_{chapter_num:02d}.mp3"
            output_path = self.create_audiobook_from_bytes(chapter_audio_bytes, chapter_info, filename)

            if output_path:
                chapter_files.append(output_path)
                logger.info(f"Created chapter {chapter_num}: {output_path}")

        return chapter_files

    def add_metadata(self, audio_file: str, metadata: Dict[str, Any]) -> None:
        """
        Add metadata to audio file.

        Args:
            audio_file: Path to audio file
            metadata: Dictionary with metadata (title, artist, album, etc.)
        """
        try:
            # Load audio
            audio = AudioSegment.from_mp3(audio_file)

            # Export with metadata
            audio.export(audio_file, format="mp3", bitrate="128k", tags=metadata)

            logger.info(f"Added metadata to {audio_file}")
        except Exception as e:
            logger.error(f"Failed to add metadata to {audio_file}: {e}")

    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        """
        Get information about an audio file.

        Args:
            audio_file: Path to audio file

        Returns:
            Dictionary with audio information
        """
        try:
            audio = AudioSegment.from_mp3(audio_file)
            return {
                "duration_seconds": len(audio) / 1000,
                "duration_formatted": self.format_duration(len(audio) / 1000),
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "bit_depth": audio.sample_width * 8,
                "file_size": os.path.getsize(audio_file),
                "dBFS": audio.dBFS,
            }
        except Exception as e:
            logger.error(f"Failed to get audio info for {audio_file}: {e}")
            return {}

    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            import shutil

            shutil.rmtree(self.temp_dir)
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.cleanup()
