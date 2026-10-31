import tempfile
import unittest
from pathlib import Path
from askai.core.component.retrieval import (
    Document,
    VectorIndex,
    chunk_documents,
    load_csv,
    load_documents,
)


def embed(texts):
    return [
        [float("cat" in text.lower()), float("dog" in text.lower()), 0.01]
        for text in texts
    ]


class RetrievalTests(unittest.TestCase):
    def test_chunks_preserve_source_and_overlap(self):
        docs = chunk_documents([Document("abcdefghij", {"source": "file"})], 6, 2)
        self.assertEqual([d.page_content for d in docs], ["abcdef", "efghij"])
        self.assertEqual(docs[1].metadata, {"source": "file", "offset": 4})
        with self.assertRaises(ValueError):
            chunk_documents([], 2, 2)

    def test_csv_and_directory_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "examples.csv"
            path.write_text("question,answer\ncat,animal\n")
            self.assertIn("question: cat", load_csv(str(path))[0].page_content)
            self.assertEqual(
                load_documents(directory, "*.csv")[0].metadata["source"], str(path)
            )

    def test_native_vector_retrieval_persistence_and_source_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            index = VectorIndex(embed, Path(directory))
            index.replace(
                [
                    Document("cat", {"source": "cats"}),
                    Document("dog", {"source": "dogs"}),
                ]
            )
            self.assertEqual(index.search("cat", 1)[0].metadata["source"], "cats")
            reopened = VectorIndex(embed, Path(directory))
            self.assertEqual(reopened.search("dog", 1)[0].page_content, "dog")
            reopened.replace([Document("cat updated", {"source": "cats"})])
            self.assertEqual(len(reopened.search("dog", 5)), 1)

    def test_ephemeral_indexes_do_not_share_documents(self):
        first, second = VectorIndex(embed), VectorIndex(embed)
        first.replace([Document("cat")])
        self.assertEqual(second.search("cat", 3), [])
