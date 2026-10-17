"""Tests for Jarvis Speech-to-Text (STT) engine."""

import pytest
from jarvis.audio.stt import MockSTT, MicrophoneSTT, get_stt_engine


def test_mock_stt_queue_behavior():
    """Verify MockSTT yields inputs in FIFO order and then returns None."""
    inputs = ["hello jarvis", "what is the time", "exit"]
    stt = MockSTT(inputs)

    assert stt.listen() == "hello jarvis"
    assert stt.listen() == "what is the time"
    assert stt.listen() == "exit"
    assert stt.listen() is None  # Queue exhausted


def test_mock_stt_add_input():
    """Verify dynamic input injection into MockSTT."""
    stt = MockSTT()
    assert stt.listen() is None

    stt.add_input("dynamic command")
    assert stt.listen() == "dynamic command"
    assert stt.listen() is None


def test_microphone_stt_initialization():
    """Verify MicrophoneSTT initializes hardware connectors cleanly."""
    stt = MicrophoneSTT()
    # It should either be available or safely report status without throwing unhandled exceptions
    avail = stt.is_available()
    assert isinstance(avail, bool)


def test_stt_factory():
    """Verify get_stt_engine returns expected instances."""
    mock = get_stt_engine("mock")
    assert isinstance(mock, MockSTT)

    default = get_stt_engine()
    assert isinstance(default, MicrophoneSTT)
