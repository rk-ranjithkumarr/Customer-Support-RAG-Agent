"""LLM wrapper. Streams from Claude if a key is set; otherwise uses an offline extractive fallback."""
import re
from typing import Iterator
from . import config

SYSTEM = f"""You are a friendly, precise customer support agent for {config.COMPANY}.
Answer ONLY using the numbered CONTEXT passages. Cite sources inline like [1] or [2].
If the context does not contain the answer, say you are not sure and offer to create a support ticket.
Be concise (under 150 words), use short steps for how-to questions, never invent policies, prices, or links."""


class LLM:
    def __init__(self):
        self.client = None
        if config.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            except Exception as e:
                print(f"[llm] Anthropic unavailable, using offline mode: {e}")

    @property
    def mode(self) -> str:
        return f"claude:{config.ANTHROPIC_MODEL}" if self.client else "offline-extractive"

    def stream(self, question: str, context: str, history: list[dict]) -> Iterator[str]:
        if self.client:
            try:
                messages = history + [{"role": "user",
                                       "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}]
                with self.client.messages.stream(model=config.ANTHROPIC_MODEL, max_tokens=500,
                                                 system=SYSTEM, messages=messages) as s:
                    for text in s.text_stream:
                        yield text
                return
            except Exception as e:
                print(f"[llm] API error, falling back to offline mode: {e}")
        yield from self._extractive(question, context)

    @staticmethod
    def _extractive(question: str, context: str) -> Iterator[str]:
        """No-LLM fallback: return the most relevant sentences from the retrieved context."""
        stop = {"the", "a", "an", "is", "to", "how", "do", "i", "my", "can", "what", "of", "in", "for", "and", "or"}
        q_terms = set(re.findall(r"[a-z0-9]+", question.lower())) - stop
        scored = []
        for m in re.finditer(r"\[(\d+)\][^\n]*\n(.*?)(?=\n\[\d+\]|\Z)", context, re.S):
            n, body = m.group(1), m.group(2)
            for s in re.split(r"(?<=[.!?])\s+|\n+", body):
                s = s.strip("-* #\t")
                if len(s) < 25:
                    continue
                overlap = len(q_terms & set(re.findall(r"[a-z0-9]+", s.lower())))
                scored.append((overlap, n, s))
        scored.sort(key=lambda t: -t[0])
        best = [t for t in scored[:3] if t[0] > 0] or scored[:2]
        text = "Here's what I found in our help center:\n\n" + "\n".join(f"- {s} [{n}]" for _, n, s in best)
        for tok in re.findall(r"\S+\s*", text):
            yield tok
