"""End-to-end integration test for the complete Jarvis voice assistant loop."""

from jarvis.audio.stt import MockSTT
from jarvis.audio.tts import MockTTS
from jarvis.config import JarvisConfig
from jarvis.core.assistant import JarvisAssistant
from jarvis.intelligence.router import IntelligenceRouter


def test_jarvis_e2e_consecutive_interaction_loop():
    """Verify that Jarvis starts, greets, processes 4 consecutive queries, and shuts down cleanly."""
    mock_tts = MockTTS()
    mock_stt = MockSTT([
        "hello jarvis",
        "what time is it",
        "who was Isaac Newton",
        "goodbye jarvis",
    ])

    test_config = JarvisConfig(
        wake_word="",  # respond to all inputs in test
        audio_settle_delay=0.0,
    )

    assistant = JarvisAssistant(
        config=test_config,
        tts=mock_tts,
        stt=mock_stt,
        text_mode=False,
    )

    # Run the assistant (it should process all 4 inputs and exit on 'goodbye jarvis')
    assistant.start()

    # Verify assistant exited cleanly
    assert assistant.is_running is False

    # Verify spoken phrases:
    # 1: Initial startup greeting ("Jarvis online and ready, sir.")
    # 2: Response to "hello jarvis"
    # 3: Response to "what time is it"
    # 4: Response to "who was Isaac Newton"
    # 5: Response to "goodbye jarvis" (shutdown)
    spoken = mock_tts.spoken_history
    assert len(spoken) >= 5, f"Expected at least 5 spoken responses, got {len(spoken)}: {spoken}"

    # Verify specific responses
    assert "ready, sir" in spoken[0].lower() or "online" in spoken[0].lower()
    assert any("sir" in s.lower() or "help" in s.lower() for s in spoken[1:2])
    assert any("time is" in s.lower() for s in spoken[2:3])
    assert any("newton" in s.lower() or "physicist" in s.lower() or "mathematician" in s.lower() for s in spoken[3:4])
    assert any("goodbye" in s.lower() or "offline" in s.lower() or "shutting down" in s.lower() or "powering down" in s.lower() for s in spoken[4:])
