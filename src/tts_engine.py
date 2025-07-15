import os
import time
from google.cloud import texttospeech

# Certifique-se de que a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS está configurada!


def synthesize_text(
    text, output_filename="output.mp3", language_code="pt-BR", ssml_gender="FEMALE"
):
    """
    Converte texto em voz e salva em um arquivo de áudio.

    Args:
        text (str): O texto a ser sintetizado.
        output_filename (str): O nome do arquivo de saída (ex: "audio.mp3").
        language_code (str): O código do idioma (ex: "en-US", "pt-BR").
        ssml_gender (str): Gênero da voz (MALE, FEMALE, NEUTRAL).
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Escolha da voz
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=ssml_gender,
        # Você também pode especificar um nome de voz específico, por exemplo:
        # name="pt-BR-Wavenet-A"
    )

    # Configurações do áudio
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Salva o áudio no arquivo
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Áudio salvo em "{output_filename}"')


if __name__ == "__main__":
    text_to_convert = "Olá! Este é um exemplo de texto convertido para voz usando o Google Text-to-Speech."
    synthesize_text(
        text_to_convert,
        f"output/meu_audio_ptbr_${time.time()}.mp3",
        language_code="pt-BR",
        ssml_gender="FEMALE",
    )

    # Exemplo com outra voz ou idioma
    # synthesize_text("Hello! This is an example of text converted to speech using Google Text-to-Speech.",
    #                 "my_audio_enus.mp3", language_code="en-US", ssml_gender="MALE")
