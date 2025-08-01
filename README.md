# fast-sttext

Convert text files to high-quality audiobooks using Google Text-to-Speech API.

## Environment Setup

### Prerequisites
- Python 3.8+
- Google Cloud account with Text-to-Speech API enabled
- ffmpeg for audio processing

### Installation
```bash
# Clone repository
git clone https://github.com/diogobarrel/fast-sttext.git
cd fast-sttext

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install ffmpeg (Ubuntu/Debian)
sudo apt install ffmpeg
```

### Google Cloud Setup
1. Create a Google Cloud project
2. Enable the Text-to-Speech API
3. Create a service account key
4. Download the JSON key file
5. Set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

## Repository Documentation

### Project Structure
```
fast-sttext/
├── src/
│   ├── main.py              # Main CLI application
│   ├── config.py            # Configuration settings
│   ├── file_handler.py      # File reading (TXT, PDF, EPUB)
│   ├── text_processor.py    # Text processing and segmentation
│   ├── tts_engine.py        # Google TTS integration
│   └── audio_processor.py   # Audio processing and merging
├── input/                   # Input files directory
├── output/                  # Generated audiobooks
└── requirements.txt         # Python dependencies
```

### Supported Formats
- Text files: `.txt`, `.md`
- eBooks: `.epub`, `.pdf`

### Configuration
Default settings in `src/config.py`:
- Language: Portuguese (pt-BR)
- Voice: Female
- Audio: MP3 format
- Premium Wavenet voices enabled

## Usage Instructions

### Basic Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Generate audiobook from text file
python -m src.main generate input/my_book.txt

# With custom output name
python -m src.main generate input/book.txt --output "audiobook.mp3"
```

### Advanced Options
```bash
# Different language and voice
python -m src.main generate input/book.txt --language "en-US" --voice "MALE"

# Split into chapter files
python -m src.main generate input/book.txt --chapters

# Preview mode (first few segments only)
python -m src.main generate input/book.txt --preview
```

### Additional Commands
```bash
# List available voices
python -m src.main voices --language "pt-BR"

# List input files
python -m src.main files

# Clean output directory
python -m src.main cleanup
```

### Python API Example
```python
from src.main import AudiobookGenerator

# Create generator
generator = AudiobookGenerator(
    language="pt-BR",
    voice_gender="FEMALE",
    premium_voices=True
)

# Generate audiobook
output_files = generator.generate_audiobook(
    "input/my_book.txt",
    output_name="my_audiobook.mp3"
)
```

### Common Issues
- **Authentication Error**: Check GOOGLE_APPLICATION_CREDENTIALS path
- **ffmpeg Not Found**: Install with `sudo apt install ffmpeg`
- **NLTK Data Missing**: Run `python -c "import nltk; nltk.download('punkt')"`
