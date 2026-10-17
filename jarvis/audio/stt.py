"""Speech-to-Text (STT) implementations for Jarvis.

Provides modular speech recognition engines:
- MicrophoneSTT: Listens via local computer microphone using speech_recognition
  (Google Web Speech API or local Whisper), with ambient noise calibration and timeout safety.
- MockSTT: Queue-driven input simulator for automated unit tests without hardware.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger("jarvis.audio.stt")


class BaseSTT(ABC):
    """Abstract base class for speech recognition engines."""

    @abstractmethod
    def listen(self, timeout: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """Capture and transcribe speech to text.

        Args:
            timeout: Maximum seconds to wait for phrase to start before timing out.
            phrase_time_limit: Maximum duration in seconds of spoken phrase to record.

        Returns:
            Transcribed text in lowercase, or None if silence/unintelligible/timeout.
        """
        pass

    @abstractmethod
    def calibrate_ambient_noise(self, duration: float = 1.0) -> bool:
        """Calibrate microphone sensitivity against room ambient noise."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if hardware / speech backend is operational."""
        pass


class MicrophoneSTT(BaseSTT):
    """Live microphone capture using SpeechRecognition."""

    def __init__(
        self,
        backend: str = "google",
        energy_threshold: int = 300,
        pause_threshold: float = 0.8,
        default_timeout: float = 6.0,
        default_phrase_limit: float = 10.0,
    ):
        self.backend = backend.lower().strip()
        self.default_timeout = default_timeout
        self.default_phrase_limit = default_phrase_limit

        self._recognizer = None
        self._microphone = None
        self._is_calibrated = False

        self._init_audio()

    def _init_audio(self) -> None:
        try:
            import speech_recognition as sr

            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.8

            self._microphone = sr.Microphone()
            logger.info("Microphone STT initialized with backend '%s'", self.backend)
        except Exception as e:
            logger.error("Failed to initialize microphone STT: %s", e)
            self._recognizer = None
            self._microphone = None

    def is_available(self) -> bool:
        return self._recognizer is not None and self._microphone is not None

    def calibrate_ambient_noise(self, duration: float = 1.0) -> bool:
        if not self.is_available():
            return False

        try:
            with self._microphone as source:
                logger.info("Calibrating microphone for ambient noise (%s sec)...", duration)
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)
                self._is_calibrated = True
                logger.info("Microphone calibrated. Energy threshold set to %s", self._recognizer.energy_threshold)
                return True
        except Exception as e:
            logger.warning("Microphone ambient noise calibration failed: %s", e)
            return False

    def listen(self, timeout: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        if not self.is_available():
            logger.error("Microphone is not available for listening.")
            return None

        import speech_recognition as sr

        t_out = timeout if timeout is not None else self.default_timeout
        p_limit = phrase_time_limit if phrase_time_limit is not None else self.default_phrase_limit

        try:
            with self._microphone as source:
                # First-time auto-calibration if not done yet
                if not self._is_calibrated:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.8)
                    self._is_calibrated = True

                logger.debug("Listening for voice input (timeout=%ss, phrase_limit=%ss)...", t_out, p_limit)
                audio_data = self._recognizer.listen(
                    source,
                    timeout=t_out,
                    phrase_time_limit=p_limit,
                )

            # Transcribe audio using selected backend
            return self._transcribe(audio_data)

        except sr.WaitTimeoutError:
            # Normal silence timeout when user hasn't spoken
            logger.debug("Listening timed out: no speech detected within %s seconds.", t_out)
            return None
        except Exception as e:
            logger.warning("Microphone capture encountered an error: %s", e)
            return None

    def _transcribe(self, audio_data) -> Optional[str]:
        import speech_recognition as sr

        try:
            if self.backend == "whisper":
                text = self._recognizer.recognize_whisper(audio_data)
            else:
                # Default to Google Speech Recognition (free, reliable, fast)
                text = self._recognizer.recognize_google(audio_data)

            if text and text.strip():
                result = text.strip()
                logger.info("Transcribed audio: '%s'", result)
                return result
            return None

        except sr.UnknownValueError:
            logger.debug("Speech was unintelligible or noise only.")
            return None
        except sr.RequestError as e:
            logger.error("STT service request error: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected transcription error: %s", e)
            return None


class MockSTT(BaseSTT):
    """Test STT that yields predetermined inputs from a queue."""

    def __init__(self, inputs: Optional[List[str]] = None):
        self.inputs: List[str] = list(inputs or [])
        self.recorded_listen_calls = 0

    def add_input(self, text: str) -> None:
        self.inputs.append(text)

    def listen(self, timeout: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        self.recorded_listen_calls += 1
        if self.inputs:
            return self.inputs.pop(0)
        return None

    def calibrate_ambient_noise(self, duration: float = 1.0) -> bool:
        return True

    def is_available(self) -> bool:
        return True


def get_stt_engine(engine_name: Optional[str] = None, **kwargs) -> BaseSTT:
    """Factory to retrieve requested STT engine."""
    name = (engine_name or "").lower().strip()
    if name == "mock":
        return MockSTT()
    return MicrophoneSTT(backend=name or "google", **kwargs)
