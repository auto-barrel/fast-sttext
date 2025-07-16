#!/usr/bin/env python3
"""
Simple example script demonstrating the audiobook generator.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.main import AudiobookGenerator


def main():
    """Simple example usage."""

    # Check for Google Cloud credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("Please set up Google Cloud credentials first")
        return

    # Create sample text file
    sample_text = """
    Capítulo 1: Introdução
    
    Este é um exemplo de texto que será convertido em audiobook.
    O sistema é capaz de detectar capítulos automaticamente.
    
    Suporta parágrafos múltiplos e faz pausas apropriadas entre sentenças.
    A qualidade do áudio é excelente graças ao Google Text-to-Speech.
    
    Capítulo 2: Funcionalidades
    
    O sistema possui várias funcionalidades interessantes:
    - Processamento inteligente de texto
    - Divisão automática em capítulos
    - Normalização de áudio
    - Metadados automáticos
    
    A geração é rápida e eficiente para textos de qualquer tamanho.
    """

    # Save sample text
    sample_file = "input/test_doc.txt"
    # Generate audiobook
    generator = None
    try:
        generator = AudiobookGenerator(
            language="pt-BR", voice_gender="FEMALE", premium_voices=True
        )

        print("🎤 Generating audiobook...")
        output_files = generator.generate_audiobook(
            sample_file,
            output_name="sample_audiobook.mp3",
            split_chapters=False,
            preview_mode=True,  # Only first 5 segments for demo
        )

        if output_files:
            print("Success! Generated audiobook:")
            for file in output_files:
                if file:
                    print(f"  {file}")
        else:
            print("Failed to generate audiobook")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if generator:
            generator.cleanup()


if __name__ == "__main__":
    main()
