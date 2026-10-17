"""Base interfaces and data structures for intelligence engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AnswerResult:
    """Standardized response from an intelligence engine."""

    # Spoken/text response for the user
    text: str

    # Whether this command signals Jarvis to terminate the session
    should_exit: bool = False

    # Name of the engine/source that generated this answer
    source: str = "core"

    # Contextual metadata to store in conversation memory
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseEngine(ABC):
    """Abstract base class for answer processing engines."""

    @abstractmethod
    def can_handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Return True if this engine can process the given query."""
        pass

    @abstractmethod
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AnswerResult:
        """Process the query and return an AnswerResult."""
        pass
