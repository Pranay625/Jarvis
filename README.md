# Jarvis — Personal Desktop Voice Assistant

A reliable, modular personal desktop voice assistant built in Python. Jarvis listens to your voice via your computer microphone, understands your spoken commands, answers questions using live web knowledge, and speaks responses aloud through your speakers.

---

## Key Features

- **Reliable Voice Interaction**: Built with a direct Windows Native SAPI driver (`win32com.client.Dispatch("SAPI.SpVoice")`) and a synchronized fallback engine (`pyttsx3`). Solves the infamous speech-freeze bug where assistants go silent after the first utterance.
- **Accurate Speech-to-Text**: Real-time microphone capture with ambient room noise calibration and timeout safety using `SpeechRecognition`.
- **Live Web Question Answering**: Answers factual questions ("Who was Alan Turing?", "What is quantum computing?") using Wikipedia's REST and search APIs and DuckDuckGo, summarizing answers into concise 1–2 spoken sentences.
- **Conversational Memory**: Retains multi-turn dialogue context for natural follow-ups ("tell me more about that").
- **Graceful Lifecycle Management**: Clean shutdown via spoken voice commands ("exit", "quit", "goodbye Jarvis", "shut down") or `Ctrl+C`.
- **Zero Echo / Audio Collision**: Incorporates post-speech settling delays to prevent microphone feedback loops.
- **Hardware Diagnostic Suite & Text Mode**: Includes standalone diagnostic tools and a keyboard fallback mode for quiet environments or headless development.

---

## Project Structure

```
Jarvis/
├── main.py                     # Primary root entrypoint
├── requirements.txt            # Project dependencies
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Documentation & setup guide
├── jarvis/
│   ├── __init__.py             # Package init
│   ├── config.py               # Settings and environment defaults
│   ├── main.py                 # CLI interface and argument parsing
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── tts.py              # Windows SAPI, pyttsx3, and Mock TTS engines
│   │   └── stt.py              # Microphone capture and Mock STT engines
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── base.py             # Base engine interface & AnswerResult
│   │   ├── rule_engine.py      # Greetings, time, date, status, exit commands
│   │   ├── knowledge_engine.py # Wikipedia & DuckDuckGo web question answering
│   │   ├── memory.py           # Multi-turn conversational context
│   │   └── router.py           # Central intelligence coordinator
│   └── core/
│       ├── __init__.py
│       ├── assistant.py        # Main interaction loop & state machine
│       └── logger.py           # Console logging
└── tests/
    ├── test_tts.py             # TTS consecutive speech tests
    ├── test_stt.py             # STT capture and error-handling tests
    ├── test_commands.py        # Rule engine & exit command tests
    ├── test_knowledge.py       # Web QA & sentence formatting tests
    ├── test_memory.py          # Conversational memory tests
    ├── test_assistant_e2e.py   # Full multi-turn loop integration test
    └── test_interactive.py     # Interactive hardware test script
```

---

## Quick Start & Installation

### 1. Requirements
- Python 3.10+ (tested on Python 3.12)
- Windows 10/11 (or macOS/Linux with fallback drivers)
- Working microphone and speakers

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Hardware (Recommended First Step)
Run the built-in audio diagnostic test to verify your speakers and microphone before starting:
```bash
python main.py --test-audio
```
This tests:
1. **TTS Output**: Speaks 3 consecutive phrases aloud to ensure speech output does not freeze or mute.
2. **STT Input**: Calibrates ambient noise and listens to a 5-second sample from your microphone.

---

## Running Jarvis

### 1. Full Voice Mode (Microphone + Speakers)
```bash
python main.py
```
- Jarvis will greet you: *"Jarvis online and ready, sir."*
- Calibrate room noise automatically for 1 second.
- Speak commands naturally into your microphone.

### 2. Keyboard / Text Mode (Quiet Mode)
If you are in a quiet room, don't have a microphone plugged in, or want to test via keyboard:
```bash
python main.py --text-mode
```
Jarvis will prompt you in the terminal (`You (text) > `) and speak its responses aloud.

### 3. Wake Word Activation (Optional)
By default, Jarvis listens to all spoken input. If you prefer Jarvis to only respond when addressed:
```bash
python main.py --wake-word jarvis
```
Example: *"Jarvis, what is the time?"*

---

## Spoken Commands

| Category | Example Voice Commands | What Jarvis Does |
|---|---|---|
| **Greetings** | *"Hello"*, *"Good morning"*, *"How are you"* | Responds with conversational greeting |
| **Time & Date** | *"What time is it?"*, *"What is today's date?"* | Announces current local time or date |
| **Identity** | *"Who are you?"*, *"What can you do?"* | Explains capabilities and identity |
| **Web Knowledge** | *"Who was Alan Turing?"*, *"What is quantum computing?"*, *"Where is Tokyo?"* | Searches Wikipedia & DuckDuckGo, speaks concise 1–2 sentence summary |
| **Follow-Up** | *"Tell me more about that"*, *"Continue"* | Uses conversation memory to provide additional details |
| **Shutdown** | *"Exit"*, *"Quit"*, *"Goodbye Jarvis"*, *"Shut down"* | Speaks farewell and terminates cleanly |

You can also press `Ctrl+C` in your terminal at any time for an immediate clean exit.

---

## Running the Automated Test Suite

Jarvis includes a comprehensive automated test suite verifying audio drivers, speech recognition fallbacks, intelligence routing, and multi-turn loops:

```bash
python -m pytest -v
```

All 19 automated unit and end-to-end integration tests execute without requiring physical audio hardware.
