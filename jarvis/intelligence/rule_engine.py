"""Rule-based engine for core assistant commands, greetings, time, and shutdown."""

import datetime
import random
from typing import Any, Dict, Optional
from jarvis.intelligence.base import BaseEngine, AnswerResult


class RuleEngine(BaseEngine):
    """Handles deterministic local commands without network dependencies."""

    EXIT_TRIGGERS = {
        "exit",
        "quit",
        "goodbye",
        "bye",
        "bye bye",
        "shut down",
        "shutdown",
        "stop",
        "terminate",
        "go to sleep",
        "close",
    }

    GREETING_TRIGGERS = {
        "hello",
        "hi",
        "hey",
        "greetings",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "how are you doing",
        "what's up",
    }

    TIME_TRIGGERS = {
        "time",
        "what time",
        "current time",
        "tell me the time",
        "what time is it",
    }

    DATE_TRIGGERS = {
        "date",
        "today's date",
        "what is the date",
        "what day is today",
        "what day is it",
        "what's the date",
    }

    IDENTITY_TRIGGERS = {
        "who are you",
        "what is your name",
        "what are you",
        "introduce yourself",
        "who made you",
    }

    HELP_TRIGGERS = {
        "help",
        "what can you do",
        "capabilities",
        "features",
        "commands",
    }

    def can_handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        q = (query or "").lower().strip()
        if not q:
            return False

        # Check exact or trigger matches
        if self._is_exit_command(q):
            return True
        if self._matches_any(q, self.TIME_TRIGGERS):
            return True
        if self._matches_any(q, self.DATE_TRIGGERS):
            return True
        if self._matches_any(q, self.GREETING_TRIGGERS):
            return True
        if self._matches_any(q, self.IDENTITY_TRIGGERS):
            return True
        if self._matches_any(q, self.HELP_TRIGGERS):
            return True

        return False

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AnswerResult:
        q = (query or "").lower().strip()

        # 1. Exit / Shutdown
        if self._is_exit_command(q):
            farewells = [
                "Goodbye, sir. Shutting down systems.",
                "Powering down. Have a productive day, sir.",
                "Offline. Standing by until next time.",
            ]
            return AnswerResult(
                text=random.choice(farewells),
                should_exit=True,
                source="rule_engine:exit",
            )

        # 2. Time
        if self._matches_any(q, self.TIME_TRIGGERS):
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p").lstrip("0")
            return AnswerResult(
                text=f"The time is {time_str}.",
                source="rule_engine:time",
            )

        # 3. Date
        if self._matches_any(q, self.DATE_TRIGGERS):
            now = datetime.datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            return AnswerResult(
                text=f"Today is {date_str}.",
                source="rule_engine:date",
            )

        # 4. Identity
        if self._matches_any(q, self.IDENTITY_TRIGGERS):
            return AnswerResult(
                text="I am Jarvis, your personal AI voice assistant. I can answer questions, provide information, and assist your daily workflow.",
                source="rule_engine:identity",
            )

        # 5. Help / Capabilities
        if self._matches_any(q, self.HELP_TRIGGERS):
            return AnswerResult(
                text="You can ask me for the time, date, general knowledge, web searches, or say exit to shut down.",
                source="rule_engine:help",
            )

        # 6. Greetings
        if self._matches_any(q, self.GREETING_TRIGGERS):
            if "how are you" in q:
                return AnswerResult(
                    text="All systems are operating at peak efficiency, sir. How may I assist you today?",
                    source="rule_engine:greeting",
                )
            responses = [
                "Hello, sir. How can I help you?",
                "Greetings, sir. Ready for your command.",
                "Hello, sir! What would you like to know today?",
            ]
            return AnswerResult(
                text=random.choice(responses),
                source="rule_engine:greeting",
            )

        return AnswerResult(
            text="I did not quite catch that command, sir.",
            source="rule_engine:fallback",
        )

    def _is_exit_command(self, query: str) -> bool:
        # Match words or phrases
        words = query.split()
        if any(w in self.EXIT_TRIGGERS for w in words):
            return True
        return any(trigger in query for trigger in self.EXIT_TRIGGERS)

    def _matches_any(self, query: str, triggers: set) -> bool:
        for t in triggers:
            # Check for substring match or word match
            if t in query:
                return True
        return False
