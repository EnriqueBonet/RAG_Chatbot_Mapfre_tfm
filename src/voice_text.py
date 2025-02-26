from google.cloud import speech



def speechtotext() -> speech.RecognizeResponse:
    # Instantiates a client
    client = speech.SpeechClient()

    # The name of the audio file to transcribe
    gcs_uri = "" # voz del usuario


    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="es",
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    # Get first result's transcript
    if response.results:
        return response.results[0].alternatives[0].transcript
    return ""


if __name__ == "__main__":
    text = speechtotext()
    print(f"Transcribed text: {text}")