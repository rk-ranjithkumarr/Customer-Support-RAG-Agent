"""The support agent: retrieve -> decide (answer or escalate) -> stream answer."""
import re
from collections import defaultdict, deque
from typing import Iterator
from . import config
from .llm import LLM
from .loader import load_knowledge_base
from .retriever import Retriever

HUMAN_RE = re.compile(
    r"\b(human|real person|live agent|representative|supervisor|manager|complaint|lawyer|legal action|"
    r"speak to (an? )?(agent|person)|talk to (an? )?(agent|person))\b", re.I)
GREET_RE = re.compile(r"^\s*(hi|hello|hey|good (morning|afternoon|evening)|thanks|thank you)\b[\s!.?]*$", re.I)


class SupportAgent:
    def __init__(self):
        self.retriever = Retriever(config.RETRIEVER)
        self.llm = LLM()
        self.sessions: dict[str, deque] = defaultdict(lambda: deque(maxlen=8))
        self.reindex()

    def reindex(self) -> int:
        chunks = load_knowledge_base(config.KB_DIR)
        self.retriever.build(chunks)
        print(f"[agent] indexed {len(chunks)} chunks | retriever={config.RETRIEVER} | llm={self.llm.mode}")
        return len(chunks)

    def _query(self, session_id: str, message: str) -> str:
        """Short follow-ups ('and for annual plans?') get the previous user turn prepended."""
        if len(message.split()) < 6:
            prev = [m["content"] for m in self.sessions[session_id] if m["role"] == "user"]
            if prev:
                return f"{prev[-1]} {message}"
        return message

    def _remember(self, sid: str, user: str, reply: str):
        self.sessions[sid].append({"role": "user", "content": user})
        self.sessions[sid].append({"role": "assistant", "content": reply})

    def handle(self, session_id: str, message: str) -> Iterator[dict]:
        message = message.strip()

        if GREET_RE.match(message):
            yield {"type": "token", "text": f"Hi! I'm the {config.COMPANY} support assistant. Ask me about billing, plans, account access, or the API."}
            yield {"type": "done", "escalate": False, "confidence": 1.0}
            return

        if HUMAN_RE.search(message):
            reply = "Of course - I'll connect you with a human agent. Please leave your email and I'll open a ticket."
            yield {"type": "token", "text": reply}
            self._remember(session_id, message, reply)
            yield {"type": "done", "escalate": True, "confidence": 0.0}
            return

        hits = self.retriever.search(self._query(session_id, message), config.TOP_K)
        top = hits[0][1] if hits else 0.0

        if not hits or top < config.MIN_SCORE:
            reply = ("I couldn't find a reliable answer in our knowledge base, so I don't want to guess. "
                     "I can open a ticket for our support team - just share your email.")
            yield {"type": "token", "text": reply}
            self._remember(session_id, message, reply)
            yield {"type": "done", "escalate": True, "confidence": round(top, 3)}
            return

        good = [(c, s) for c, s in hits if s >= config.MIN_SCORE * 0.6]
        context = "\n\n".join(f"[{i}] ({c.source})\n{c.text}" for i, (c, _) in enumerate(good, 1))
        yield {"type": "sources", "sources": [
            {"n": i, "source": c.source, "score": round(s, 3), "snippet": c.text[:220]}
            for i, (c, s) in enumerate(good, 1)]}

        parts = []
        for tok in self.llm.stream(message, context, list(self.sessions[session_id])):
            parts.append(tok)
            yield {"type": "token", "text": tok}
        self._remember(session_id, message, "".join(parts))
        yield {"type": "done", "escalate": False, "confidence": round(top, 3)}

    def transcript(self, session_id: str) -> str:
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self.sessions[session_id])
