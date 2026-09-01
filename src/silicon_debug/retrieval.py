from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

from .schemas import Evidence

_TOKENS = re.compile(r"[A-Za-z0-9_+-]{2,}")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKENS.findall(text)]


@dataclass(frozen=True)
class SearchHit:
    evidence: Evidence
    score: float


class BM25Index:
    """Small, deterministic in-memory BM25 index for bounded local corpora."""

    def __init__(self, documents: Iterable[Evidence]):
        self.documents = list(documents)
        self.tokens = [tokenize(doc.text) for doc in self.documents]
        self.avgdl = sum(map(len, self.tokens)) / max(1, len(self.tokens))
        self.df: dict[str, int] = {}
        for tokens in self.tokens:
            for token in set(tokens):
                self.df[token] = self.df.get(token, 0) + 1

    def search(self, query: str, top_k: int = 5) -> list[SearchHit]:
        top_k = max(1, min(top_k, 20))
        q_tokens = tokenize(query)
        scores: list[SearchHit] = []
        n = max(1, len(self.documents))
        for doc, tokens in zip(self.documents, self.tokens):
            frequencies = {token: tokens.count(token) for token in set(tokens)}
            score = 0.0
            for token in q_tokens:
                tf = frequencies.get(token, 0)
                if not tf:
                    continue
                idf = math.log(1 + (n - self.df.get(token, 0) + 0.5) / (self.df.get(token, 0) + 0.5))
                score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * len(tokens) / max(1, self.avgdl)))
            if score > 0:
                scores.append(SearchHit(doc, round(score, 6)))
        return sorted(scores, key=lambda hit: (-hit.score, hit.evidence.evidence_id))[:top_k]

