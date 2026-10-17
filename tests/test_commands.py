"""Tests for Jarvis rule-based commands and basic conversation."""

from jarvis.intelligence.rule_engine import RuleEngine


def test_greeting_commands():
    engine = RuleEngine()
    assert engine.can_handle("hello")
    assert engine.can_handle("good morning jarvis")
    assert engine.can_handle("how are you")

    res = engine.process("hello")
    assert res.should_exit is False
    assert len(res.text) > 0
    assert "sir" in res.text.lower() or "help" in res.text.lower() or "hello" in res.text.lower()


def test_time_and_date_commands():
    engine = RuleEngine()
    assert engine.can_handle("what is the time")
    assert engine.can_handle("what day is today")

    time_res = engine.process("what time is it")
    assert "time is" in time_res.text.lower()
    assert time_res.should_exit is False

    date_res = engine.process("what is today's date")
    assert "today is" in date_res.text.lower()
    assert date_res.should_exit is False


def test_exit_commands():
    engine = RuleEngine()
    exit_queries = ["exit", "quit", "goodbye", "shut down", "bye"]
    for q in exit_queries:
        assert engine.can_handle(q), f"Failed to detect exit trigger: {q}"
        res = engine.process(q)
        assert res.should_exit is True, f"Expected should_exit=True for query: {q}"


def test_identity_and_help():
    engine = RuleEngine()
    assert engine.can_handle("who are you")
    assert engine.can_handle("what can you do")

    res_id = engine.process("who are you")
    assert "jarvis" in res_id.text.lower()
    assert res_id.should_exit is False
