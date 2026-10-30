"""Load documents from the knowledge base and split them into chunks."""
import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED = {".md", ".txt", ".pdf"}


@dataclass
class Chunk:
    id: str
    source: str
    text: str


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, source: str, max_words: int = 140) -> list[Chunk]:
    """Heading-aware paragraph chunking. Each chunk keeps its section heading for context."""
    chunks, heading, buf, words = [], "", [], 0

    def flush():
        nonlocal buf, words
        if buf:
            body = "\n".join(buf).strip()
            full = f"{heading}\n{body}".strip() if heading else body
            chunks.append(Chunk(f"{source}#{len(chunks)}", source, full))
        buf, words = [], 0

    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if para.startswith("#"):
            flush()
            lines = para.split("\n", 1)
            heading = lines[0].lstrip("# ").strip()
            para = lines[1].strip() if len(lines) > 1 else ""
            if not para:
                continue
        n = len(para.split())
        if words + n > max_words and buf:
            flush()
        buf.append(para)
        words += n
    flush()
    return chunks


def load_knowledge_base(kb_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            try:
                chunks.extend(chunk_text(read_file(path), path.name))
            except Exception as e:  # never let one bad file break indexing
                print(f"[loader] skipped {path.name}: {e}")
    return chunks
