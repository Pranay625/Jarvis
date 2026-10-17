"""Web-based Question Answering (QA) engine for Jarvis.

Fetches factual knowledge using Wikipedia REST/Search APIs and DuckDuckGo,
summarizing responses to 1-2 concise, spoken-friendly sentences.
"""

import logging
import re
import urllib.parse
from typing import Any, Dict, Optional
import requests
from jarvis.intelligence.base import AnswerResult, BaseEngine

logger = logging.getLogger("jarvis.intelligence.knowledge")


class KnowledgeEngine(BaseEngine):
    """Retrieves factual information from open web sources with robust fallbacks."""

    USER_AGENT = "JarvisVoiceAssistant/1.0 (Desktop Assistant; contact: jarvis-assistant@local)"
    TIMEOUT_SECONDS = 5.0

    # Common query prefixes to strip when searching topics
    QUESTION_PREFIXES = [
        r"^who\s+(?:is|was|were)\s+",
        r"^what\s+(?:is|was|are|were)\s+(?:a|an|the)?\s*",
        r"^where\s+(?:is|was|are|were)\s+",
        r"^when\s+(?:did|was|is)\s+",
        r"^tell\s+me\s+about\s+",
        r"^define\s+",
        r"^explain\s+",
        r"^search\s+for\s+",
        r"^can\s+you\s+tell\s+me\s+about\s+",
    ]

    def can_handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        q = (query or "").lower().strip()
        if len(q) < 3:
            return False

        # If it's a follow-up ("tell me more", "more details") and we have context
        if context and context.get("last_topic") and any(phrase in q for phrase in ["more about that", "tell me more", "continue"]):
            return True

        # Matches question keywords
        question_words = ["who", "what", "where", "when", "why", "how", "tell me about", "explain", "define"]
        return any(q.startswith(qw) or f" {qw} " in q for qw in question_words)

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AnswerResult:
        q = (query or "").strip()

        # Handle follow-up query if user said "tell me more"
        if context and context.get("last_topic") and any(phrase in q.lower() for phrase in ["more about", "tell me more", "continue"]):
            topic = context["last_topic"]
            full_extract = context.get("last_full_extract", "")
            if full_extract:
                second_part = self._extract_followup_sentence(full_extract)
                if second_part:
                    return AnswerResult(
                        text=second_part,
                        source="knowledge:followup",
                        metadata={"last_topic": topic, "last_full_extract": full_extract},
                    )

        topic = self._extract_topic(q)
        logger.info("Searching knowledge base for topic: '%s' (from query: '%s')", topic, q)

        # 1. Try Wikipedia direct summary or search
        wiki_result = self._query_wikipedia(topic)
        if wiki_result:
            clean_text, full_text = wiki_result
            return AnswerResult(
                text=clean_text,
                source="knowledge:wikipedia",
                metadata={"last_topic": topic, "last_full_extract": full_text},
            )

        # 2. Try DuckDuckGo Instant Answer
        ddg_result = self._query_duckduckgo(topic)
        if ddg_result:
            return AnswerResult(
                text=ddg_result,
                source="knowledge:duckduckgo",
                metadata={"last_topic": topic},
            )

        # 3. Graceful fallback when no results found
        return AnswerResult(
            text=f"I searched for {topic}, but could not find a verified answer, sir.",
            source="knowledge:empty",
            metadata={"last_topic": topic},
        )

    def _extract_topic(self, query: str) -> str:
        """Strip filler question phrases to isolate the search entity/subject."""
        cleaned = query.strip().rstrip("?.!")
        for pattern in self.QUESTION_PREFIXES:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned if cleaned else query.strip().rstrip("?.!")

    def _query_wikipedia(self, topic: str) -> Optional[tuple[str, str]]:
        """Query Wikipedia API with multi-step search & summary resolution."""
        headers = {"User-Agent": self.USER_AGENT}

        # Step A: Direct summary attempt for known title
        formatted_topic = urllib.parse.quote(topic.replace(" ", "_"))
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_topic}"
        try:
            resp = requests.get(summary_url, headers=headers, timeout=self.TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract", "")
                if extract:
                    spoken = self._format_spoken_summary(extract)
                    return spoken, extract
        except Exception as e:
            logger.debug("Wikipedia direct summary failed: %s", e)

        # Step B: OpenSearch fallback for search queries
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": topic,
            "limit": "2",
            "namespace": "0",
            "format": "json",
        }
        try:
            s_resp = requests.get(search_url, params=params, headers=headers, timeout=self.TIMEOUT_SECONDS)
            if s_resp.status_code == 200:
                s_data = s_resp.json()
                # s_data structure: [query, [titles], [descriptions], [urls]]
                if len(s_data) > 1 and s_data[1]:
                    best_title = s_data[1][0]
                    # Fetch summary for best match
                    best_formatted = urllib.parse.quote(best_title.replace(" ", "_"))
                    sec_resp = requests.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{best_formatted}",
                        headers=headers,
                        timeout=self.TIMEOUT_SECONDS,
                    )
                    if sec_resp.status_code == 200:
                        data = sec_resp.json()
                        extract = data.get("extract", "")
                        if extract:
                            spoken = self._format_spoken_summary(extract)
                            return spoken, extract
        except Exception as e:
            logger.warning("Wikipedia OpenSearch lookup failed: %s", e)

        return None

    def _query_duckduckgo(self, query: str) -> Optional[str]:
        """Query DuckDuckGo Instant Answer API as a secondary source."""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        headers = {"User-Agent": self.USER_AGENT}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=self.TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("Answer") or data.get("AbstractText") or ""
                if answer:
                    return self._format_spoken_summary(answer)
        except Exception as e:
            logger.debug("DuckDuckGo query error: %s", e)
        return None

    def _format_spoken_summary(self, raw_text: str, max_sentences: int = 2) -> str:
        """Format raw text into clean, natural spoken sentences."""
        if not raw_text:
            return ""

        # Remove bracketed citations like [1], [2], [citation needed]
        text = re.sub(r"\[[^\]]*\]", "", raw_text)
        # Remove parenthetical phonetic/pronunciation artifacts and parenthetical dates
        text = re.sub(r"\([^)]*\)", "", text)
        # Normalize whitespace
        text = " ".join(text.split())

        # Split into sentences (handles '.', '!', '?')
        sentences = re.split(r"(?<=[.!?])\s+", text)
        selected = sentences[:max_sentences]
        spoken = " ".join(selected).strip()

        # Ensure sentence has closing punctuation
        if spoken and spoken[-1] not in ".!?":
            spoken += "."

        return spoken

    def _extract_followup_sentence(self, full_extract: str) -> Optional[str]:
        """Extract subsequent sentences for 'tell me more' queries."""
        sentences = re.split(r"(?<=[.!?])\s+", full_extract)
        if len(sentences) > 2:
            return " ".join(sentences[2:4]).strip()
        return "I have shared all the primary details available on this topic, sir."
