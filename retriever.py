"""Retrieval layer: TF-IDF (default, zero downloads) or sentence-transformer embeddings."""
import threading
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .loader import Chunk


class Retriever:
    def __init__(self, mode: str = "tfidf"):
        self.mode = mode
        self.chunks: list[Chunk] = []
        self._lock = threading.Lock()
        self._model = None
        self._vec = None
        self._matrix = None

    def build(self, chunks: list[Chunk]) -> None:
        texts = [c.text for c in chunks]
        vec = matrix = None
        if texts:
            if self.mode == "embeddings":
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer("all-MiniLM-L6-v2")
                matrix = self._model.encode(texts, normalize_embeddings=True)
            else:
                vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True,
                                      stop_words="english")
                matrix = vec.fit_transform(texts)
        with self._lock:  # atomic swap -> searches never see a half-built index
            self.chunks, self._vec, self._matrix = chunks, vec, matrix

    def search(self, query: str, k: int = 4) -> list[tuple[Chunk, float]]:
        with self._lock:
            chunks, vec, matrix = self.chunks, self._vec, self._matrix
        if not chunks or matrix is None:
            return []
        if self.mode == "embeddings":
            q = self._model.encode([query], normalize_embeddings=True)
            scores = (matrix @ q.T).ravel()
        else:
            scores = cosine_similarity(vec.transform([query]), matrix).ravel()
        idx = np.argsort(scores)[::-1][:k]
        return [(chunks[i], float(scores[i])) for i in idx]
