# Fast-STText: Audiobook Generator

🎤 **Converts text files to high-quality audiobooks to help you study when you can't read**

A comprehensive Python application that transforms text files into professional audiobooks using Google Cloud Text-to-Speech API with intelligent text processing and advanced audio manipulation.

## ✨ Features

- 📚 **Multiple Input Formats**: Supports TXT, MD, PDF, and EPUB files
- 🎭 **Premium Voice Options**: Access to Google's WaveNet voices for natural-sounding speech
- 🌍 **Multi-language Support**: Support for Portuguese, English, and many other languages
- 📖 **Chapter Detection**: Automatically detects and separates chapters
- 🎵 **Audio Processing**: Professional audio normalization, fade effects, and proper pauses
- 🔄 **Batch Processing**: Efficient processing of large texts with progress tracking
- **Metadata Support**: Automatic metadata addition to generated audiobooks
- 🎛️ **Customizable Settings**: Configurable voice, speaking rate, pitch, and more
- **Preview Mode**: Generate previews with first few segments before full conversion
- **Chapter Splitting**: Option to create separate audio files for each chapter

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud Account**: Set up a Google Cloud project with Text-to-Speech API enabled
2. **Python 3.8+**: Make sure you have Python 3.8 or higher installed
3. **ffmpeg**: Required for audio processing (installation instructions below)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/diogobarrel/fast-sttext.git
cd fast-sttext
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install ffmpeg**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS (with Homebrew)
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. **Set up Google Cloud credentials**:
```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"

# Or add to your ~/.bashrc or ~/.zshrc
echo 'export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"' >> ~/.bashrc
```

### Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Text-to-Speech API
4. Create a service account and download the JSON key file
5. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## 📖 Usage

### Command Line Interface

The application provides a comprehensive CLI interface:

```bash
# Generate audiobook from text file
python -m src.main generate input/my_book.txt

# Generate with custom settings
python -m src.main generate input/my_book.txt \
  --output "my_audiobook.mp3" \
  --language "en-US" \
  --voice "MALE" \
  --premium \
  --chapters

# Preview mode (first 5 segments only)
python -m src.main generate input/my_book.txt --preview

# List available voices
python -m src.main voices --language "pt-BR"

# List input files
python -m src.main files

# Clean up output directory
python -m src.main cleanup
```

### Python API

```python
from src.main import AudiobookGenerator

# Initialize generator
generator = AudiobookGenerator(
    language="pt-BR",
    voice_gender="FEMALE",
    premium_voices=True
)

# Generate audiobook
output_files = generator.generate_audiobook(
    input_file="input/my_book.txt",
    output_name="my_audiobook.mp3",
    split_chapters=False,
    preview_mode=False
)

# Clean up
generator.cleanup()
```

### Simple Example

Run the included example:

```bash
python example.py
```

This will create a sample text file and generate a preview audiobook.

## Project Structure

```
fast-sttext/
├── src/
│   ├── main.py              # Main application and CLI
│   ├── tts_engine.py        # Google TTS integration
│   ├── text_processor.py    # Text processing and segmentation
│   ├── audio_processor.py   # Audio manipulation and effects
│   ├── file_handler.py      # File I/O operations
│   └── config.py           # Configuration settings
├── input/                   # Place your text files here
├── output/                  # Generated audiobooks appear here
├── requirements.txt         # Python dependencies
├── example.py              # Simple usage example
└── README.md               # This file
```

## ⚙️ Configuration

Edit `src/config.py` to customize:

- **Voice Settings**: Default language, gender, and voice names
- **Audio Settings**: Speaking rate, pitch, volume, and pause durations
- **Processing Settings**: Chunk size, supported formats
- **File Paths**: Input/output directories

## 🎭 Available Voices

The system supports multiple voice types:

- **Standard Voices**: Good quality, lower cost
- **WaveNet Voices**: Premium quality, more natural-sounding
- **Multiple Languages**: Portuguese, English, Spanish, French, and more
- **Gender Options**: Male, Female, Neutral

List available voices:
```bash
python -m src.main voices --language "pt-BR"
```

## Supported File Formats

### Input Formats
- **Text Files**: `.txt`, `.md`
- **PDF Files**: `.pdf` (text extraction)
- **EPUB Files**: `.epub` (ebook format)

### Output Formats
- **MP3**: High-quality compressed audio
- **Metadata**: Automatic title, artist, and genre information

## 🔧 Advanced Features

### Chapter Detection
The system automatically detects chapters using patterns like:
- `Capítulo 1: Title`
- `Chapter 1: Title`
- `1. Title`
- `Parte 1: Title`

### Text Processing
- **Smart Segmentation**: Intelligent paragraph and sentence splitting
- **Abbreviation Handling**: Expands common abbreviations
- **Number Processing**: Proper pronunciation of numbers
- **SSML Support**: Enhanced speech control with pauses and emphasis

### Audio Processing
- **Normalization**: Consistent volume levels
- **Fade Effects**: Professional fade-in and fade-out
- **Pause Management**: Appropriate pauses between sentences and chapters
- **Metadata**: Automatic ID3 tag addition

## 🚨 Troubleshooting

### Common Issues

1. **Google Cloud Credentials Error**:
   ```
   Make sure GOOGLE_APPLICATION_CREDENTIALS is set correctly
   ```

2. **ffmpeg Not Found**:
   ```bash
   # Install ffmpeg first
   sudo apt install ffmpeg  # Ubuntu/Debian
   brew install ffmpeg      # macOS
   ```

3. **Import Errors**:
   ```bash
   # Make sure all dependencies are installed
   pip install -r requirements.txt
   ```

4. **Audio Quality Issues**:
   - Use premium WaveNet voices for better quality
   - Adjust speaking rate and pitch in config

### Logging

The application creates detailed logs in `audiobook_generator.log` for debugging.

## 💡 Tips for Best Results

1. **Text Preparation**:
   - Remove unnecessary formatting
   - Use clear chapter markers
   - Check for typos and abbreviations

2. **Voice Selection**:
   - Use WaveNet voices for better quality
   - Test different voices for your content

3. **Performance**:
   - Use preview mode for testing
   - Process large files in chunks
   - Monitor API usage and costs

## Performance

- **Processing Speed**: ~1000 characters per second
- **Audio Quality**: 128kbps MP3, 22kHz sample rate
- **Memory Usage**: Efficient streaming for large files
- **Cost**: Depends on Google Cloud TTS pricing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## Acknowledgments

- Google Cloud Text-to-Speech API
- pydub library for audio processing
- NLTK for text processing
- Click for CLI interface

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the logs for detailed error information

---

**Made with ❤️ to help you study better!**
The project should be able to receive inputs as large text files or input strings and convert them to audio (.mp3) files, helping me listen and study even when I can’t read.
