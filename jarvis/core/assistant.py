"""Main Jarvis Voice Assistant orchestrator and lifecycle controller."""

import logging
import signal
import sys
import time
from typing import Optional

from jarvis.audio.stt import BaseSTT, get_stt_engine
from jarvis.audio.tts import BaseTTS, get_tts_engine
from jarvis.config import JarvisConfig, config as default_config
from jarvis.intelligence.router import IntelligenceRouter

logger = logging.getLogger("jarvis.core.assistant")


class JarvisAssistant:
    """Orchestrates audio capture, intelligence routing, speech synthesis, and session state."""

    def __init__(
        self,
        config: Optional[JarvisConfig] = None,
        tts: Optional[BaseTTS] = None,
        stt: Optional[BaseSTT] = None,
        router: Optional[IntelligenceRouter] = None,
        text_mode: bool = False,
    ):
        self.config = config or default_config
        self.text_mode = text_mode
        self.is_running = False

        # Initialize TTS
        if tts is not None:
            self.tts = tts
        else:
            self.tts = get_tts_engine(
                engine_name=self.config.tts_engine,
                rate=self.config.voice_rate,
                volume=self.config.voice_volume,
            )

        # Initialize STT
        if stt is not None:
            self.stt = stt
        else:
            self.stt = get_stt_engine(
                engine_name=self.config.stt_engine,
                energy_threshold=self.config.mic_energy_threshold,
                pause_threshold=self.config.mic_pause_threshold,
                default_timeout=self.config.listen_timeout,
                default_phrase_limit=self.config.phrase_time_limit,
            )

        # Initialize Intelligence Router
        self.router = router or IntelligenceRouter(self.config)

        # Setup OS signal handlers for clean Ctrl+C shutdown
        self._setup_signals()

    def _setup_signals(self) -> None:
        """Register signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGINT, self._handle_interrupt)
            signal.signal(signal.SIGTERM, self._handle_interrupt)
        except (ValueError, AttributeError):
            # In non-main threads or some environments, signal registration might not be allowed
            pass

    def _handle_interrupt(self, signum, frame) -> None:
        """Handle SIGINT (Ctrl+C) gracefully."""
        print("\n[Jarvis] Interrupt signal received. Shutting down gracefully...")
        logger.info("Interrupt signal received (%s). Terminating Jarvis session.", signum)
        self.is_running = False
        try:
            self.tts.speak("Goodbye, sir.")
        except Exception:
            pass
        sys.exit(0)

    def start(self) -> None:
        """Start the Jarvis voice assistant session."""
        self.is_running = True
        mode_label = "Keyboard / Text Mode" if self.text_mode else "Full Voice Mode (Mic + Speaker)"
        print("=" * 60)
        print(f"  JARVIS PERSONAL ASSISTANT ONLINE ({mode_label})")
        print(f"  TTS Engine : {self.tts.__class__.__name__}")
        print(f"  STT Engine : {self.stt.__class__.__name__}")
        print(f"  Mode       : {mode_label}")
        print(f"  Wake Word  : '{self.config.wake_word}' (or speak freely)")
        print("  Press Ctrl+C or say 'exit' / 'quit' to terminate.")
        print("=" * 60)

        # 1. Initial Spoken Greeting
        greeting = "Jarvis online and ready, sir."
        print(f"\nJarvis > {greeting}")
        self.tts.speak(greeting)

        # 2. Microphone ambient noise calibration (if in voice mode)
        if not self.text_mode and self.stt.is_available():
            print("[Calibrating microphone for room ambient noise...]")
            self.stt.calibrate_ambient_noise(duration=0.8)
            print("[Calibration complete. Ready for voice commands.]")

        # 3. Main Interaction Loop
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.is_running:
            try:
                # Capture user input
                query = self._get_input()

                if query is None:
                    # Silence timeout or no input detected, loop back to listen
                    consecutive_errors = 0
                    continue

                consecutive_errors = 0
                query_clean = query.strip()
                if not query_clean:
                    continue

                print(f"\nYou > {query_clean}")

                # Process wake word if configured
                processed_query = self._filter_wake_word(query_clean)
                if processed_query is None:
                    # Utterance did not address Jarvis
                    continue

                if not processed_query:
                    # User only said the wake word ("Jarvis")
                    acknowledgment = "Yes, sir. I am listening."
                    print(f"Jarvis > {acknowledgment}")
                    self.tts.speak(acknowledgment)
                    self._settle_delay()
                    continue

                # Route query through intelligence router
                answer_result = self.router.route(processed_query)

                # Output response
                print(f"Jarvis > {answer_result.text} (Source: {answer_result.source})")

                # Vocalize response
                self.tts.speak(answer_result.text)

                # Audio settling delay to prevent echo pickup
                self._settle_delay()

                # Clean exit on shutdown command
                if answer_result.should_exit:
                    logger.info("Shutdown command detected. Ending session.")
                    self.is_running = False
                    break

            except KeyboardInterrupt:
                self._handle_interrupt(signal.SIGINT, None)
                break
            except Exception as e:
                logger.error("Error encountered in interaction cycle: %s", e, exc_info=True)
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical("Exceeded maximum consecutive errors. Halting assistant.")
                    self.tts.speak("Critical system error encountered. Shutting down, sir.")
                    self.is_running = False
                    break
                time.sleep(0.5)

        print("\n[Jarvis session finished. Systems offline.]")

    def _get_input(self) -> Optional[str]:
        """Obtain input via keyboard or microphone depending on mode."""
        if self.text_mode:
            try:
                text = input("\nYou (text) > ")
                return text.strip() if text.strip() else None
            except EOFError:
                self.is_running = False
                return "exit"
        else:
            return self.stt.listen()

    def _filter_wake_word(self, query: str) -> Optional[str]:
        """Check and strip wake word if enabled."""
        wake_word = (self.config.wake_word or "").lower().strip()
        if not wake_word:
            # Wake word is disabled; process all speech
            return query

        q_lower = query.lower().strip()

        # Check if query starts with wake word
        if q_lower.startswith(wake_word):
            remainder = q_lower[len(wake_word) :].strip(" ,.:;!?")
            return remainder

        # If wake word is present anywhere in query, strip it
        if wake_word in q_lower:
            parts = q_lower.split(wake_word, 1)
            return (parts[0] + " " + parts[1]).strip(" ,.:;!?")

        # If wake word is required but was not detected, return None
        return None

    def _settle_delay(self) -> None:
        """Brief pause after speaking before microphone opens to prevent echo loop."""
        delay = getattr(self.config, "audio_settle_delay", 0.25)
        if delay > 0 and not self.text_mode:
            time.sleep(delay)
