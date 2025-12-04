"""
Whisper STT Provider for Sisters-Multilingual-Coach
"""

import os
from typing import Optional
from openai import OpenAI


class WhisperSTT:
    """Speech-to-Text using OpenAI Whisper API"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "whisper-1"

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file (mp3, wav, etc.)
            language: Optional language hint (en, zh, ja, ko, es)

        Returns:
            Dict with transcription result
        """
        with open(audio_path, "rb") as audio_file:
            kwargs = {
                "model": self.model,
                "file": audio_file,
                "response_format": "verbose_json"
            }

            if language:
                kwargs["language"] = language

            response = self.client.audio.transcriptions.create(**kwargs)

        return {
            "text": response.text,
            "language": response.language,
            "duration": response.duration,
            "segments": response.segments if hasattr(response, 'segments') else []
        }

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio from bytes

        Args:
            audio_bytes: Audio data as bytes
            filename: Filename hint for format detection
            language: Optional language hint

        Returns:
            Dict with transcription result
        """
        # Save temporarily
        temp_path = f"/tmp/{filename}"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        try:
            result = self.transcribe(temp_path, language)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return result
