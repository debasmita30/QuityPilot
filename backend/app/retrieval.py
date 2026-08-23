import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_DIR = Path(__file__).parent / "data" / "documents"


@dataclass
class Chunk:
    doc_id: str
    title: str
    status: str
    scope: str
    effective_date: str
    heading: str
    text: str
    chunk_id: str = field(default="")


def _parse_document(path: Path) -> tuple[dict, str]:
    raw = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.DOTALL)
    if not match:
        return {}, raw
    meta = yaml.safe_load(match.group(1))
    return meta, match.group(2)


def _split_sections(body: str) -> list[tuple[str, str]]:
    sections = []
    current_heading = "Overview"
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return [(h, t) for h, t in sections if t]


class DocumentIndex:
    def __init__(self, docs_dir: Path = DOCS_DIR):
        self.chunks: list[Chunk] = []
        self._load(docs_dir)
        corpus = [f"{c.title} {c.heading} {c.text}" for c in self.chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=4000)
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _load(self, docs_dir: Path) -> None:
        for path in sorted(docs_dir.glob("*.md")):
            meta, body = _parse_document(path)
            for i, (heading, text) in enumerate(_split_sections(body)):
                self.chunks.append(
                    Chunk(
                        doc_id=meta.get("doc_id", path.stem),
                        title=meta.get("title", path.stem),
                        status=meta.get("status", "current"),
                        scope=meta.get("scope", "general"),
                        effective_date=str(meta.get("effective_date", "")),
                        heading=heading,
                        text=text,
                        chunk_id=f"{meta.get('doc_id', path.stem)}::{i}",
                    )
                )

    def search(
        self,
        query: str,
        account_scope: Optional[str] = None,
        include_deprecated: bool = False,
        top_k: int = 6,
    ) -> list[dict]:
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix)[0]

        scored = []
        for chunk, sim in zip(self.chunks, sims):
            if sim <= 0:
                continue
            if chunk.status == "deprecated" and not include_deprecated:
                continue
            score = float(sim)
            if chunk.scope == "general":
                score *= 1.0
            elif account_scope and chunk.scope == f"account:{account_scope}":
                score *= 1.6
            else:
                score *= 0.15
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            results.append(
                {
                    "doc_id": chunk.doc_id,
                    "title": chunk.title,
                    "status": chunk.status,
                    "scope": chunk.scope,
                    "effective_date": chunk.effective_date,
                    "heading": chunk.heading,
                    "text": chunk.text,
                    "relevance": round(score, 4),
                }
            )
        return results


_index: Optional[DocumentIndex] = None


def get_index() -> DocumentIndex:
    global _index
    if _index is None:
        _index = DocumentIndex()
    return _index
