"""Text-to-Speech (TTS) engine implementations for Jarvis.

Provides modular, resilient speech synthesis engines:
- WindowsSAPITTS: High-reliability Windows Native SAPI via COM (immune to pyttsx3 event loop deadlocks).
- Pyttsx3TTS: Cross-platform fallback using pyttsx3 with managed event loop state.
- MockTTS: In-memory voice simulator for headless testing and CI.
"""

import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger("jarvis.audio.tts")


class BaseTTS(ABC):
    """Abstract base class for speech synthesis engines."""

    @abstractmethod
    def speak(self, text: str) -> bool:
        """Speak the given text aloud.

        Args:
            text: Spoken string to vocalize.

        Returns:
            True if speech completed successfully, False otherwise.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Interrupt and stop current speech playback."""
        pass

    @abstractmethod
    def get_voices(self) -> List[str]:
        """Return list of available voice names."""
        pass


class WindowsSAPITTS(BaseTTS):
    """Native Windows Speech API (SAPI.SpVoice) via COM.

    Resolves the infamous pyttsx3 consecutive-speech freeze by using direct
    Windows SAPI COM bindings. Each speak() call runs synchronously, ensuring
    clean audio endpoint release before subsequent microphone capture starts.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0, voice_index: int = 0):
        self._voice = None
        self._rate_wpm = rate
        self._volume = volume
        self._voice_index = voice_index
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            self._voice = win32com.client.Dispatch("SAPI.SpVoice")

            # SAPI Rate scale is -10 (slowest) to +10 (fastest), where 0 is default (~150 wpm).
            # Map standard WPM (~100 to ~300) to SAPI (-10 to +10):
            sapi_rate = max(-10, min(10, int((self._rate_wpm - 150) / 15)))
            self._voice.Rate = sapi_rate

            # SAPI Volume is integer 0 to 100:
            sapi_volume = max(0, min(100, int(self._volume * 100)))
            self._voice.Volume = sapi_volume

            # Set voice if specified
            voices = self._voice.GetVoices()
            if 0 <= self._voice_index < voices.Count:
                self._voice.Voice = voices.Item(self._voice_index)

            logger.info("Windows SAPI TTS initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize Windows SAPI TTS: %s", e)
            self._voice = None

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        try:
            import pythoncom

            pythoncom.CoInitialize()
            if self._voice is None:
                self._init_engine()

            if self._voice is None:
                logger.warning("SAPI voice engine unavailable. Text not spoken: %s", text)
                return False

            # Flag 0 = SVSFDefault (synchronous speech - blocks until audio completes)
            # This ensures zero audio buffer overlap with subsequent microphone input.
            self._voice.Speak(text.strip(), 0)
            return True
        except Exception as e:
            logger.error("Error during SAPI speech output: %s", e)
            # Try to recover engine for subsequent calls
            self._init_engine()
            return False

    def stop(self) -> None:
        if self._voice is not None:
            try:
                # Flag 2 = SVSFPurgeBeforeSpeak
                self._voice.Speak("", 2)
            except Exception as e:
                logger.debug("Error stopping SAPI speech: %s", e)

    def get_voices(self) -> List[str]:
        if self._voice is None:
            return []
        try:
            voices = self._voice.GetVoices()
            return [voices.Item(i).GetDescription() for i in range(voices.Count)]
        except Exception as e:
            logger.warning("Could not list SAPI voices: %s", e)
            return []


class Pyttsx3TTS(BaseTTS):
    """Cross-platform pyttsx3 fallback with protected single-thread execution."""

    def __init__(self, rate: int = 180, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._engine = None
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
            logger.info("pyttsx3 TTS initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize pyttsx3 engine: %s", e)
            self._engine = None

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        try:
            if self._engine is None:
                self._init_engine()

            if self._engine is None:
                logger.warning("pyttsx3 engine unavailable. Text not spoken: %s", text)
                return False

            self._engine.say(text.strip())
            self._engine.runAndWait()
            return True
        except Exception as e:
            logger.error("pyttsx3 speech failure: %s", e)
            # Recreate engine in case of corrupted event loop
            try:
                self._init_engine()
            except Exception:
                pass
            return False

    def stop(self) -> None:
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass

    def get_voices(self) -> List[str]:
        if not self._engine:
            return []
        try:
            voices = self._engine.getProperty("voices")
            return [v.name for v in voices]
        except Exception:
            return []


class MockTTS(BaseTTS):
    """Test engine that records speech in memory without hardware output."""

    def __init__(self):
        self.spoken_history: List[str] = []
        self.is_stopped = False

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        cleaned = text.strip()
        self.spoken_history.append(cleaned)
        logger.debug("[MockTTS] Spoke: '%s'", cleaned)
        return True

    def stop(self) -> None:
        self.is_stopped = True

    def get_voices(self) -> List[str]:
        return ["Mock Voice 1 (English)", "Mock Voice 2 (British)"]

    def clear(self) -> None:
        """Clear recorded speech history."""
        self.spoken_history.clear()


def get_tts_engine(engine_name: Optional[str] = None, rate: int = 180, volume: float = 1.0) -> BaseTTS:
    """Factory to create appropriate TTS engine based on OS and configuration."""
    name = (engine_name or "").lower().strip()

    if name == "mock":
        return MockTTS()

    if sys.platform == "win32" and (name == "sapi" or not name):
        try:
            return WindowsSAPITTS(rate=rate, volume=volume)
        except Exception as e:
            logger.warning("Falling back from SAPI to pyttsx3: %s", e)

    # Cross-platform fallback
    try:
        return Pyttsx3TTS(rate=rate, volume=volume)
    except Exception as e:
        logger.warning("Falling back to MockTTS: %s", e)
        return MockTTS()
