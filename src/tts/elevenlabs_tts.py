"""
ElevenLabs TTS Provider for Sisters-Multilingual-Coach
Updated for ElevenLabs SDK v1.x
"""

import os
from typing import Optional
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Ensure .env is loaded
load_dotenv()


class ElevenLabsTTS:
    """Text-to-Speech using ElevenLabs API"""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set in environment")

        self.client = ElevenLabs(api_key=self.api_key)

        # Voice IDs for each character + user example (can be customized)
        self.voice_ids = {
            "Botan": os.getenv("ELEVENLABS_VOICE_ID_BOTAN", "21m00Tcm4TlvDq8ikWAM"),
            "Kasho": os.getenv("ELEVENLABS_VOICE_ID_KASHO", "AZnzlk1XvdvUeBnXmlld"),
            "Yuri": os.getenv("ELEVENLABS_VOICE_ID_YURI", "EXAVITQu4vr4xnSDxMaL"),
            "Ojisan": os.getenv("ELEVENLABS_VOICE_ID_USER", "scOwDtmlUjD3prqpp97I"),  # Sam (male) for Ojisan
            "User": os.getenv("ELEVENLABS_VOICE_ID_USER", "scOwDtmlUjD3prqpp97I"),  # Sam (male) for example
        }

        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

        # Debug: Print all voice IDs on init
        print(f"[TTS INIT] Voice IDs loaded: {self.voice_ids}")
        print(f"[TTS INIT] Model: {self.model}")

    def generate_speech(
        self,
        text: str,
        sister: str = "Botan",
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate speech from text using ElevenLabs

        Args:
            text: Text to convert to speech
            sister: Which sister's voice to use (Botan, Kasho, Yuri)
            output_path: Optional path to save audio file

        Returns:
            Audio data as bytes
        """
        voice_id = self.voice_ids.get(sister, self.voice_ids["Botan"])
        print(f"[TTS] Sister: {sister}, Voice ID: {voice_id}")  # Debug

        # Generate audio using new SDK API
        audio_generator = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=self.model,
            voice_settings={
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        )

        # Convert generator to bytes
        audio_bytes = b"".join(audio_generator)

        # Save to file if path provided
        if output_path:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

        return audio_bytes

    def get_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs"""
        voices = self.client.voices.get_all()
        return [{"id": v.voice_id, "name": v.name} for v in voices.voices]
