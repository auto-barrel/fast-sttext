#!/bin/bash

# Setup script for fast-sttext audiobook generator

echo "🚀 Setting up fast-sttext audiobook generator..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📋 Python version: $python_version"

# Check if Python 3.8+ is available
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "Python 3.8+ is available"
else
    echo "Python 3.8+ is required"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p input output

# Check for ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is installed"
else
    echo " ffmpeg is not installed. Please install it:"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   macOS: brew install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/download.html"
fi

# Check for Google Cloud credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Google Cloud credentials are set"
else
    echo " Google Cloud credentials not found"
    echo "   Please set GOOGLE_APPLICATION_CREDENTIALS environment variable"
    echo "   Example: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json"
fi

# Create sample text file
echo "Creating sample text file..."
cat > input/sample.txt << 'EOF'
Capítulo 1: Introdução ao Sistema

Este é um exemplo de texto que será convertido em audiobook usando o fast-sttext.

O sistema utiliza a API do Google Text-to-Speech para gerar áudio de alta qualidade.
Ele pode processar textos em português, inglês e muitos outros idiomas.

Capítulo 2: Funcionalidades

As principais funcionalidades incluem:
- Detecção automática de capítulos
- Processamento inteligente de texto
- Normalização de áudio
- Suporte a múltiplos formatos

O resultado é um audiobook profissional que pode ser usado para estudos.
EOF

echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set up Google Cloud credentials"
echo "3. Install ffmpeg if not already installed"
echo "4. Run the example: python example.py"
echo "5. Or use the CLI: python -m src.main generate input/sample.txt"
echo ""
echo "For more information, check the README.md file."
