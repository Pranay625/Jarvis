"""Router dispatching spoken queries to appropriate intelligence engines."""

import logging
from typing import Optional
from jarvis.config import JarvisConfig, config as default_config
from jarvis.intelligence.base import AnswerResult
from jarvis.intelligence.knowledge_engine import KnowledgeEngine
from jarvis.intelligence.memory import ConversationMemory
from jarvis.intelligence.rule_engine import RuleEngine

logger = logging.getLogger("jarvis.intelligence.router")


class IntelligenceRouter:
    """Dispatches user queries across rule and knowledge engines."""

    def __init__(self, config: Optional[JarvisConfig] = None):
        self.config = config or default_config
        self.memory = ConversationMemory()
        self.rule_engine = RuleEngine()
        self.knowledge_engine = KnowledgeEngine()

    def route(self, query: str) -> AnswerResult:
        """Route a user query through the engine hierarchy and update memory."""
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            return AnswerResult(text="", source="router:empty")

        context = self.memory.get_context()

        # 1. Deterministic Rule Engine (Exit, greetings, time, date)
        if self.rule_engine.can_handle(cleaned_query, context):
            result = self.rule_engine.process(cleaned_query, context)
            self.memory.add_turn(cleaned_query, result)
            return result

        # 2. Web Knowledge Engine (Wikipedia + DuckDuckGo)
        if self.knowledge_engine.can_handle(cleaned_query, context):
            result = self.knowledge_engine.process(cleaned_query, context)
            self.memory.add_turn(cleaned_query, result)
            return result

        # 3. Default fallback: Attempt web search for any general phrase
        result = self.knowledge_engine.process(cleaned_query, context)
        if result.source != "knowledge:empty":
            self.memory.add_turn(cleaned_query, result)
            return result

        # 4. Polite unresolved fallback
        fallback_result = AnswerResult(
            text="I am not certain how to answer that yet, sir. You can ask me for the time, date, or facts from the web.",
            source="router:unhandled",
        )
        self.memory.add_turn(cleaned_query, fallback_result)
        return fallback_result
