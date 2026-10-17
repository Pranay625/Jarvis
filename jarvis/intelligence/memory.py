"""Conversational context and multi-turn state management for Jarvis."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from jarvis.intelligence.base import AnswerResult


@dataclass
class ConversationTurn:
    """A single turn in the voice conversation."""

    query: str
    response: str
    source: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """Maintains short-term dialogue context across consecutive interactions."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []
        self._context_state: Dict[str, Any] = {}

    def add_turn(self, query: str, answer_result: AnswerResult) -> None:
        """Record a completed user-assistant interaction turn."""
        turn = ConversationTurn(
            query=query,
            response=answer_result.text,
            source=answer_result.source,
            metadata=dict(answer_result.metadata),
        )
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)

        # Merge metadata into current context state
        if answer_result.metadata:
            self._context_state.update(answer_result.metadata)

    def get_context(self) -> Dict[str, Any]:
        """Return the current context dictionary for engines."""
        return dict(self._context_state)

    def get_last_turn(self) -> Optional[ConversationTurn]:
        """Return the most recent conversation turn, if any."""
        return self.turns[-1] if self.turns else None

    def get_recent_history(self, limit: int = 5) -> List[ConversationTurn]:
        """Return up to `limit` most recent turns."""
        return self.turns[-limit:]

    def clear(self) -> None:
        """Reset conversation memory."""
        self.turns.clear()
        self._context_state.clear()
