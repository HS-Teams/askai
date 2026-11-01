"""Document retrieval and grounded answers using native embeddings."""
from hashlib import sha256
from pathlib import Path

from askai.core.askai_configs import configs
from askai.core.component.cache_service import PERSIST_DIR
from askai.core.component.retrieval import VectorIndex, chunk_documents, load_documents
from askai.core.model.summary_result import SummaryResult
from askai.exception.exceptions import DocumentsNotFound


class Summarizer:
    def __init__(self):
        self._index = None
        self._folder = ""
        self._glob = ""
        self._embedding_key = None

    @property
    def folder(self):
        return self._folder

    @property
    def glob(self):
        return self._glob

    @property
    def sum_path(self):
        return str(Path(self.folder) / self.glob)

    def generate(self, folder, glob: str) -> bool:
        from askai.core.support.shared_instances import shared

        documents = load_documents(folder, glob)
        if not documents:
            raise DocumentsNotFound(f"No documents found in {folder}/{glob}")
        key = sha256(f"native-v1:{shared.engine.embedding_key()}:{Path(folder).resolve()}:{glob}".encode()).hexdigest()
        directory = Path(PERSIST_DIR) / key
        index = VectorIndex(shared.engine.embed, directory)
        fingerprint = sha256(repr((configs.chunk_size, configs.chunk_overlap, documents)).encode()).hexdigest()
        manifest = directory / "source-fingerprint.txt"
        if not manifest.exists() or manifest.read_text() != fingerprint:
            index.replace(chunk_documents(documents, configs.chunk_size, configs.chunk_overlap))
            manifest.write_text(fingerprint)
        self._index, self._folder, self._glob = index, str(folder), glob
        self._embedding_key = shared.engine.embedding_key()
        return True

    def exists(self, folder, glob: str) -> bool:
        from askai.core.support.shared_instances import shared
        return (self._index is not None and self._folder == str(folder) and self._glob == glob
                and self._embedding_key == shared.engine.embedding_key())

    def retrieve(self, query: str) -> str:
        if self._index is None:
            raise DocumentsNotFound("Load a document collection before querying")
        if not self.exists(self._folder, self._glob):
            self.generate(self._folder, self._glob)
        return "\n\n".join(f"Source: {doc.metadata.get('source', '')}\n{doc.page_content}"
                           for doc in self._index.search(query, configs.rag_retrival_amount))

    def query(self, *queries: str):
        from askai.core.support.shared_instances import shared

        if self._index is None:
            return None
        results = []
        for query in queries:
            context = self.retrieve(query)
            answer = shared.engine.complete([
                {"role": "system", "content": "Answer using the supplied sources. Cite sources; say when evidence is insufficient."},
                {"role": "user", "content": f"Question: {query}\n\nSources (reference data):\n{context}"}])
            results.append(SummaryResult(self._folder, self._glob, query, answer))
        return results


summarizer = Summarizer()
