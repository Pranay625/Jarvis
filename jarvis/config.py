"""Configuration settings for Jarvis Voice Assistant."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass
class JarvisConfig:
    """Jarvis assistant settings."""

    # Speech synthesis (TTS): 'sapi' (Windows native, default), 'pyttsx3' (fallback), or 'mock'
    tts_engine: str = os.getenv("JARVIS_TTS_ENGINE", "sapi").strip().lower()

    # Speech recognition (STT): 'google' (default, free & fast), 'whisper', or 'mock'
    stt_engine: str = os.getenv("JARVIS_STT_ENGINE", "google").strip().lower()

    # Voice properties
    voice_rate: int = int(os.getenv("JARVIS_VOICE_RATE", "180"))
    voice_volume: float = float(os.getenv("JARVIS_VOICE_VOLUME", "1.0"))

    # Wake word (empty or false disables wake word; responds to all speech)
    # Set to 'jarvis' to only respond when addressed
    wake_word: str = os.getenv("JARVIS_WAKE_WORD", "").strip().lower()

    # Settling delay in seconds after speaking before opening mic (prevents echo loop)
    audio_settle_delay: float = float(os.getenv("JARVIS_AUDIO_SETTLE_DELAY", "0.25"))

    # Microphone listening parameters
    mic_energy_threshold: int = int(os.getenv("JARVIS_MIC_ENERGY_THRESHOLD", "300"))
    mic_pause_threshold: float = float(os.getenv("JARVIS_MIC_PAUSE_THRESHOLD", "0.8"))
    listen_timeout: float = float(os.getenv("JARVIS_LISTEN_TIMEOUT", "6.0"))
    phrase_time_limit: float = float(os.getenv("JARVIS_PHRASE_TIME_LIMIT", "10.0"))


# Default configuration instance
config = JarvisConfig()
