"""Tests for Jarvis web question-answering engine."""

from jarvis.intelligence.knowledge_engine import KnowledgeEngine


def test_topic_extraction():
    ke = KnowledgeEngine()
    assert ke._extract_topic("who was Alan Turing") == "Alan Turing"
    assert ke._extract_topic("what is quantum computing") == "quantum computing"
    assert ke._extract_topic("tell me about python") == "python"
    assert ke._extract_topic("where is Tokyo") == "Tokyo"


def test_spoken_summary_formatting():
    ke = KnowledgeEngine()
    raw = "Alan Mathison Turing [1] (/ˈtjʊərɪŋ/; 23 June 1912 – 7 June 1954) was an English mathematician. He was highly influential in the development of theoretical computer science. He also played a pivotal role in cracking intercepted coded messages during the Second World War."
    formatted = ke._format_spoken_summary(raw, max_sentences=2)

    # Citations and phonetic pronunciation brackets removed
    assert "[1]" not in formatted
    assert "/ˈtjʊərɪŋ/" not in formatted
    assert "Alan Mathison Turing" in formatted
    # Check max 2 sentences
    assert "English mathematician" in formatted
    assert "theoretical computer science" in formatted
    # 3rd sentence should be excluded
    assert "pivotal role in cracking" not in formatted


def test_knowledge_live_query():
    """Verify live web retrieval for a known entity."""
    ke = KnowledgeEngine()
    res = ke.process("who is Albert Einstein")
    assert res.should_exit is False
    assert len(res.text) > 20
    assert "einstein" in res.text.lower() or "physicist" in res.text.lower()


def test_knowledge_empty_fallback():
    """Verify polite response when searching nonsense."""
    ke = KnowledgeEngine()
    res = ke.process("what is xyzqwe123456789nonexistentconcept")
    assert res.should_exit is False
    assert "could not find" in res.text.lower() or "searched" in res.text.lower()
