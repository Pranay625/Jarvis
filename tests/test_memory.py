"""Tests for Jarvis conversational memory and router integration."""

from jarvis.intelligence.base import AnswerResult
from jarvis.intelligence.memory import ConversationMemory
from jarvis.intelligence.router import IntelligenceRouter


def test_conversation_memory_history():
    mem = ConversationMemory(max_turns=3)
    mem.add_turn("hello", AnswerResult(text="Hello sir", source="rule_engine"))
    mem.add_turn("what time is it", AnswerResult(text="It is 10 PM", source="rule_engine"))

    assert len(mem.turns) == 2
    assert mem.get_last_turn().query == "what time is it"

    # Add 2 more turns (should evict oldest turn)
    mem.add_turn("q3", AnswerResult(text="a3", source="rule"))
    mem.add_turn("q4", AnswerResult(text="a4", source="rule"))

    assert len(mem.turns) == 3
    assert mem.turns[0].query == "what time is it"
    assert mem.turns[-1].query == "q4"


def test_router_integration():
    router = IntelligenceRouter()

    # Rule match
    res_time = router.route("what is the time")
    assert "time is" in res_time.text.lower()
    assert res_time.should_exit is False

    # Exit command
    res_exit = router.route("exit")
    assert res_exit.should_exit is True

    # Memory retention
    assert len(router.memory.turns) == 2
