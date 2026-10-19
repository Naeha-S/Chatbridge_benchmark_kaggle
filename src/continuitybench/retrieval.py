from __future__ import annotations

import math
import re
import hashlib
from collections import Counter
from typing import Sequence

Tokenized = list[str]


def _tokenize(text: str) -> Tokenized:
    return re.findall(r"[a-z0-9]+", text.lower())


class BaseRetriever:
    def __init__(self, documents: Sequence[str]):
        self.documents = list(documents)

    def retrieve(self, query: str, k: int = 5) -> list[tuple[int, str, float]]:
        raise NotImplementedError


class NoRetrievalBaseline(BaseRetriever):
    def retrieve(self, query: str, k: int = 5) -> list[tuple[int, str, float]]:
        return []


class KeywordRetriever(BaseRetriever):
    def retrieve(self, query: str, k: int = 5) -> list[tuple[int, str, float]]:
        q = set(_tokenize(query))
        scored = []
        for i, doc in enumerate(self.documents):
            d = set(_tokenize(doc))
            score = float(len(q & d))
            scored.append((i, doc, score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:k]


class BM25Retriever(BaseRetriever):
    def __init__(self, documents: Sequence[str], k1: float = 1.5, b: float = 0.75):
        super().__init__(documents)
        self.k1 = k1
        self.b = b
        self.doc_tokens = [_tokenize(d) for d in self.documents]
        self.doc_lens = [len(toks) for toks in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0.0
        self.df = Counter()
        for toks in self.doc_tokens:
            for term in set(toks):
                self.df[term] += 1

    def _idf(self, term: str) -> float:
        n_docs = len(self.documents)
        df = self.df[term]
        return math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

    def retrieve(self, query: str, k: int = 5) -> list[tuple[int, str, float]]:
        query_terms = _tokenize(query)
        scored = []
        for i, toks in enumerate(self.doc_tokens):
            tf = Counter(toks)
            score = 0.0
            for term in query_terms:
                if term not in tf:
                    continue
                numerator = tf[term] * (self.k1 + 1)
                denominator = tf[term] + self.k1 * (1 - self.b + self.b * (len(toks) / (self.avg_doc_len or 1.0)))
                score += self._idf(term) * (numerator / denominator)
            scored.append((i, self.documents[i], score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:k]


class DenseRetriever(BaseRetriever):
    def __init__(self, documents: Sequence[str], dim: int = 128):
        super().__init__(documents)
        self.dim = dim
        self._model = None
        self._doc_vectors = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            self._doc_vectors = self._model.encode(self.documents)
        except Exception:
            self._doc_vectors = [self._hash_vector(doc) for doc in self.documents]

    def _hash_vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _tokenize(text):
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            idx = int.from_bytes(digest[:8], "big") % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _encode(self, text: str):
        if self._model is not None:
            return self._model.encode([text])[0]
        return self._hash_vector(text)

    @staticmethod
    def _dot(a, b) -> float:
        return float(sum(x * y for x, y in zip(a, b)))

    def retrieve(self, query: str, k: int = 5) -> list[tuple[int, str, float]]:
        q = self._encode(query)
        scored = []
        for i, doc_vec in enumerate(self._doc_vectors or []):
            score = self._dot(q, doc_vec)
            scored.append((i, self.documents[i], score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:k]


class HybridRetriever(BaseRetriever):
    def __init__(self, documents: Sequence[str], lexical_weight: float = 0.5):
        super().__init__(documents)
        self.lexical_weight = lexical_weight
        self.bm25 = BM25Retriever(documents)
        self.dense = DenseRetriever(documents)

    @staticmethod
    def _normalize(scores: dict[int, float]) -> dict[int, float]:
        if not scores:
            return {}
        values = list(scores.values())
        lo, hi = min(values), max(values)
        if math.isclose(lo, hi):
            return {k: 0.0 for k in scores}
        return {k: (v - lo) / (hi - lo) for k, v in scores.items()}

    def retrieve(self, query: str, k: int = 5) -> list[tuple[int, str, float]]:
        lexical = {i: score for i, _, score in self.bm25.retrieve(query, k=len(self.documents))}
        dense = {i: score for i, _, score in self.dense.retrieve(query, k=len(self.documents))}
        lexical = self._normalize(lexical)
        dense = self._normalize(dense)

        scores = {}
        for i in range(len(self.documents)):
            scores[i] = self.lexical_weight * lexical.get(i, 0.0) + (1 - self.lexical_weight) * dense.get(i, 0.0)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [(i, self.documents[i], score) for i, score in ranked]


