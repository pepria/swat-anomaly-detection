"""Small retrieval layer over the markdown knowledge base.

Every ``## `` section of every file in ``knowledge_base/`` is one chunk. Retrieval
is TF-IDF cosine similarity plus a boost for chunks that mention the anomaly's
tags exactly. No external services are needed; the scorer can be swapped for an
embedding model later (``Retriever.score`` is the only place to change).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .. import config as C

TAG_RE = re.compile(r"\b(?:LIT|FIT|AIT|DPIT|PIT|MV|P|UV|LS|LSH|LSL|LSLL)\d{3}\b")


@dataclass
class Chunk:
    chunk_id: str
    source: str
    title: str
    text: str
    tags: set


def load_chunks(kb_dir: Path = C.KB_DIR) -> list[Chunk]:
    chunks = []
    for f in sorted(kb_dir.glob("*.md")):
        parts = re.split(r"^## ", f.read_text(), flags=re.M)
        for i, p in enumerate(parts[1:], 1):
            title, _, body = p.partition("\n")
            text = f"{title}\n{body}".strip()
            chunks.append(Chunk(f"{f.stem}#{i}", f.name, title.strip(), text,
                                set(TAG_RE.findall(text))))
    return chunks


class Retriever:
    def __init__(self, kb_dir: Path = C.KB_DIR, tag_boost: float = 0.15):
        self.chunks = load_chunks(kb_dir)
        # keep tag names as single tokens (LIT101, MV501 ...)
        self.vec = TfidfVectorizer(token_pattern=r"(?u)\b[A-Za-z][A-Za-z0-9_]+\b",
                                   lowercase=True, sublinear_tf=True, ngram_range=(1, 2))
        self.M = self.vec.fit_transform([c.text for c in self.chunks])
        self.tag_boost = tag_boost

    def score(self, query: str, tags: list[str]) -> np.ndarray:
        q = self.vec.transform([query])
        s = (self.M @ q.T).toarray().ravel()
        tags = set(tags)
        if tags:
            s += self.tag_boost * np.array([len(c.tags & tags) / len(tags) for c in self.chunks])
        return s

    def search(self, query: str, tags: list[str] = (), k: int = 6,
               sources: list[str] | None = None) -> list[tuple[Chunk, float]]:
        s = self.score(query, list(tags))
        order = np.argsort(-s)
        out = []
        for i in order:
            if sources and self.chunks[i].source not in sources:
                continue
            out.append((self.chunks[i], float(s[i])))
            if len(out) == k:
                break
        return out
