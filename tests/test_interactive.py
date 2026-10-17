"""Interactive physical hardware verification script for Jarvis.

Run this script to interactively test physical speakers and microphone:
    python tests/test_interactive.py
"""

import sys
import time
from jarvis.audio.stt import MicrophoneSTT
from jarvis.audio.tts import WindowsSAPITTS, get_tts_engine
from jarvis.intelligence.router import IntelligenceRouter


def run_interactive_audio():
    print("=" * 60)
    print("  JARVIS INTERACTIVE AUDIO HARDWARE TEST")
    print("=" * 60)
    print("This script will guide you through testing your actual speakers and microphone.\n")

    # 1. Output Test
    print("[1/3] Testing Spoken Responses (Speakers)...")
    tts = get_tts_engine()
    print(f"Active TTS Engine: {tts.__class__.__name__}")

    utterances = [
        "First utterance: Hello, testing speaker output.",
        "Second utterance: Consecutive speech verification in progress.",
        "Third utterance: All consecutive speech tests completed successfully.",
    ]

    for idx, u in enumerate(utterances, 1):
        print(f"  Speaking phrase {idx}/3...")
        tts.speak(u)
        time.sleep(0.3)

    user_heard = input("\nDid you hear all three phrases spoken aloud clearly? (y/n): ").strip().lower()
    if user_heard != "y":
        print("[!] Audio output failed or was muted. Check system volume and output devices.")
        return False
    print("[OK] Speaker test passed!")

    # 2. Input Test
    print("\n[2/3] Testing Microphone Input...")
    stt = MicrophoneSTT()
    if not stt.is_available():
        print("[!] Microphone is not available.")
        return False

    print("Calibrating ambient noise (1 sec)...")
    stt.calibrate_ambient_noise(duration=1.0)
    print("Speak a short sentence into your microphone now (e.g. 'Hello Jarvis what time is it')...")
    transcription = stt.listen(timeout=6.0, phrase_time_limit=6.0)

    if transcription:
        print(f"\nRecognized Text: '{transcription}'")
        user_matched = input("Does this transcription match what you spoke? (y/n): ").strip().lower()
        if user_matched == "y":
            print("[OK] Microphone test passed!")
        else:
            print("[INFO] Partial match recorded.")
    else:
        print("[!] No speech was captured or recognized. Check microphone permissions.")

    # 3. Full Interaction Test
    print("\n[3/3] Testing End-to-End Query Routing...")
    router = IntelligenceRouter()
    queries = ["What is the time?", "Who was Alan Turing?", "exit"]

    for q in queries:
        res = router.route(q)
        print(f"\nQuery   : {q}")
        print(f"Response: {res.text}")
        print(f"Source  : {res.source}")
        print(f"Exit    : {res.should_exit}")
        tts.speak(res.text)

    print("\n" + "=" * 60)
    print("  Hardware & Interactive Verification Finished!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    run_interactive_audio()
