"""CLI Entrypoint for Jarvis Voice Assistant."""

import argparse
import sys
import time

from jarvis.audio.stt import get_stt_engine
from jarvis.audio.tts import get_tts_engine
from jarvis.config import config
from jarvis.core.assistant import JarvisAssistant
from jarvis.core.logger import setup_logger


def run_audio_diagnostics():
    """Run an independent hardware diagnostic on TTS and STT before launching."""
    print("=" * 60)
    print("  JARVIS AUDIO HARDWARE DIAGNOSTIC SUITE")
    print("=" * 60)

    # 1. Test Text-to-Speech Consecutive Utterances
    print("\n[Step 1/2] Testing Speech Output (TTS) across 3 consecutive calls...")
    tts = get_tts_engine(config.tts_engine, rate=config.voice_rate, volume=config.voice_volume)
    print(f"Using TTS Engine: {tts.__class__.__name__}")

    test_phrases = [
        "Audio test utterance number one.",
        "Audio test utterance number two.",
        "Audio test utterance number three. Text to speech is operating normally.",
    ]

    for idx, phrase in enumerate(test_phrases, 1):
        print(f"  -> Speaking phrase {idx}: '{phrase}'")
        success = tts.speak(phrase)
        if not success:
            print(f"  [ERROR] TTS failed on phrase {idx}!")
            return False
        time.sleep(0.3)

    print("  [SUCCESS] All 3 consecutive speech utterances completed cleanly!")

    # 2. Test Speech Recognition & Microphone
    print("\n[Step 2/2] Testing Microphone & Speech Recognition (STT)...")
    stt = get_stt_engine(config.stt_engine)
    print(f"Using STT Engine: {stt.__class__.__name__}")

    if not stt.is_available():
        print("  [WARNING] Microphone device or recognition engine is not currently available.")
        print("  You can still run Jarvis in keyboard mode using: python main.py --text-mode")
        return False

    print("  Calibrating ambient room noise for 1 second...")
    stt.calibrate_ambient_noise(duration=1.0)
    print("  Please speak something into your microphone now (listening for 5 seconds)...")

    sample_audio = stt.listen(timeout=5.0, phrase_time_limit=5.0)
    if sample_audio:
        print(f"  [SUCCESS] Captured and transcribed: '{sample_audio}'")
    else:
        print("  [INFO] No speech detected within timeout (or microphone was silent).")
        print("  Hardware check completed.")

    print("\n" + "=" * 60)
    print("  Audio Diagnostics Completed Successfully.")
    print("=" * 60 + "\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Jarvis Personal Voice Assistant")
    parser.add_argument(
        "--text-mode",
        action="store_true",
        help="Run in interactive keyboard mode (without microphone)",
    )
    parser.add_argument(
        "--test-audio",
        action="store_true",
        help="Run audio hardware diagnostic test and exit",
    )
    parser.add_argument(
        "--wake-word",
        type=str,
        default=None,
        help="Set wake word (e.g. 'jarvis'). Leave unset to respond to all speech.",
    )
    parser.add_argument(
        "--tts-engine",
        type=str,
        choices=["sapi", "pyttsx3", "mock"],
        default=None,
        help="Select TTS engine (default: sapi on Windows)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    setup_logger(verbose=args.verbose)

    # Apply CLI overrides to configuration
    if args.wake_word is not None:
        config.wake_word = args.wake_word.strip().lower()
    if args.tts_engine:
        config.tts_engine = args.tts_engine

    # Run diagnostics if requested
    if args.test_audio:
        success = run_audio_diagnostics()
        sys.exit(0 if success else 1)

    # Launch Jarvis Assistant
    assistant = JarvisAssistant(
        config=config,
        text_mode=args.text_mode,
    )
    assistant.start()


if __name__ == "__main__":
    main()
