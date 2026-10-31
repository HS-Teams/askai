"""Native document loading, chunking and vector retrieval, independent of the view."""

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from uuid import uuid4


@dataclass(frozen=True)
class Document:
    page_content: str
    metadata: dict = field(default_factory=dict)


def load_documents(folder: str | Path, pattern: str) -> list[Document]:
    documents = []
    for path in sorted(Path(folder).glob(pattern)):
        if not path.is_file():
            continue
        if path.suffix.lower() in {
            ".md",
            ".txt",
            ".py",
            ".json",
            ".csv",
            ".yaml",
            ".yml",
            ".rst",
        }:
            text = path.read_text(encoding="utf-8")
        else:
            from unstructured.partition.auto import partition

            text = "\n\n".join(
                str(element) for element in partition(filename=str(path))
            )
        documents.append(Document(text, {"source": str(path)}))
    return documents


def load_csv(path: str) -> list[Document]:
    with open(path, encoding="utf-8", newline="") as source:
        return [
            Document(
                "\n".join(f"{key}: {value}" for key, value in row.items()),
                {"source": path, "row": index},
            )
            for index, row in enumerate(csv.DictReader(source))
        ]


def chunk_documents(
    documents: list[Document], size: int, overlap: int
) -> list[Document]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Chunk size must exceed overlap, which must be nonnegative")
    chunks = []
    for document in documents:
        for start in range(0, len(document.page_content), size - overlap):
            chunks.append(
                Document(
                    document.page_content[start : start + size],
                    {**document.metadata, "offset": start},
                )
            )
            if start + size >= len(document.page_content):
                break
    return chunks


class VectorIndex:
    def __init__(self, embed: Callable, directory: Path | None = None):
        import chromadb
        from chromadb.config import Settings

        self._embed = embed
        settings = Settings(anonymized_telemetry=False)
        self._client = (
            chromadb.PersistentClient(path=str(directory), settings=settings)
            if directory
            else chromadb.EphemeralClient(settings=settings)
        )
        self._collection = self._client.get_or_create_collection(
            name="askai_documents" if directory else f"askai_{uuid4().hex}",
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )

    def replace(self, documents: list[Document]) -> None:
        if not documents:
            raise ValueError("Cannot index an empty document collection")
        ids = [
            hashlib.sha256(
                f"{index}:{doc.metadata}:{doc.page_content}".encode()
            ).hexdigest()
            for index, doc in enumerate(documents)
        ]
        vectors = self._embed([doc.page_content for doc in documents])
        # Embed first so provider failure leaves the previous collection usable.
        self._collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=[doc.page_content for doc in documents],
            metadatas=[doc.metadata or {"source": "unknown"} for doc in documents],
        )
        stale = set(self._collection.get()["ids"]) - set(ids)
        if stale:
            self._collection.delete(ids=list(stale))

    def search(self, query: str, k: int) -> list[Document]:
        count = self._collection.count()
        if not count or k < 1:
            return []
        result = self._collection.query(
            query_embeddings=self._embed([query]), n_results=min(k, count)
        )
        return [
            Document(text, metadata)
            for text, metadata in zip(result["documents"][0], result["metadatas"][0])
        ]
