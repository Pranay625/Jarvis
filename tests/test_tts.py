"""Tests for Jarvis Text-to-Speech (TTS) engine.

Specifically verifies that multiple consecutive spoken responses execute
without deadlock, silencing, or COM errors.
"""

import sys
import pytest
from jarvis.audio.tts import MockTTS, WindowsSAPITTS, Pyttsx3TTS, get_tts_engine


def test_mock_tts_consecutive_speech():
    """Verify MockTTS records multiple consecutive phrases accurately."""
    tts = MockTTS()
    phrases = ["Greeting user", "Processing query", "Displaying results", "Shutting down"]

    for phrase in phrases:
        success = tts.speak(phrase)
        assert success is True

    assert len(tts.spoken_history) == 4
    assert tts.spoken_history == phrases


def test_mock_tts_ignores_empty():
    """Verify empty or whitespace strings are not spoken."""
    tts = MockTTS()
    assert tts.speak("") is False
    assert tts.speak("   ") is False
    assert len(tts.spoken_history) == 0


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SAPI only supported on Windows")
def test_windows_sapi_consecutive_speech():
    """Verify Windows native SAPI speaks multiple consecutive phrases without hanging.

    This directly addresses the historical assistant failure where the 1st
    phrase worked but subsequent phrases became silent or blocked.
    """
    tts = WindowsSAPITTS(rate=200, volume=0.8)
    assert tts._voice is not None, "SAPI voice failed to initialize"

    test_utterances = [
        "Diagnostic test: utterance one.",
        "Diagnostic test: utterance two.",
        "Diagnostic test: utterance three.",
    ]

    for index, utterance in enumerate(test_utterances):
        result = tts.speak(utterance)
        assert result is True, f"Speech failed on utterance {index + 1}"

    # Verify voice listing
    voices = tts.get_voices()
    assert len(voices) > 0, "Expected at least one SAPI voice installed on Windows"


def test_factory_fallback():
    """Verify engine factory defaults and fallback behavior."""
    mock = get_tts_engine("mock")
    assert isinstance(mock, MockTTS)

    engine = get_tts_engine()
    if sys.platform == "win32":
        assert isinstance(engine, (WindowsSAPITTS, Pyttsx3TTS, MockTTS))
    assert engine is not None
