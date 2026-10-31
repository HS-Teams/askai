#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.support
   @file: rag_provider.py
@created: Wed, 28 Aug 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from typing import Optional

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_settings import ASKAI_DIR
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_state
from hspylib.core.tools.commons import dirname, file_is_not_empty, safe_delete_file
from hspylib.core.tools.text_tools import ensure_endswith, hash_text
from pathlib import Path

import glob
import os
import shutil

# External RAG Directory
RAG_EXT_DIR: Path = Path(f"{ASKAI_DIR}/rag")
if not RAG_EXT_DIR.exists():
    RAG_EXT_DIR.mkdir(parents=True, exist_ok=True)


from askai.core.component.retrieval import Document, VectorIndex, load_csv


class RAGProvider:
    """A class responsible for implementing the Retrieval-Augmented Generation (RAG) mechanism."""

    RAG_DIR: Path = Path(os.path.join(classpath.resource_path, "rag"))

    @classmethod
    def copy_rag(cls, path_name: AnyPath, dest_name: AnyPath | None = None, rag_dir: AnyPath = RAG_EXT_DIR) -> bool:
        """Copy RAG documents into the specified RAG directory.
        :param path_name: The path of the RAG documents to copy.
        :param dest_name: The destination, within the RAG directory, where the documents will be copied to. If None,
                          defaults to a hashed directory based on the source path.
        :param rag_dir: The directory where RAG documents will be copied to.
        :return: True if the copy operation was successful, False otherwise.
        """
        src_path: PathObject = PathObject.of(path_name)
        if src_path.exists and src_path.is_file:
            file: str = f"{rag_dir}/{dest_name or src_path.filename}"
            shutil.copyfile(str(src_path), file)
        elif src_path.exists and src_path.is_dir:
            shutil.copytree(
                str(src_path),
                str(rag_dir / (dest_name or hash_text(str(src_path))[:8])),
                dirs_exist_ok=True,
                symlinks=True,
            )
        else:
            return False

        files: list[str] = sorted(glob.glob(f"{str(rag_dir)}/**/*.*", recursive=True))
        rag_files: str = "".join(list(ensure_endswith(d, os.linesep) for d in files))
        rag_docs_file: Path = Path(os.path.join(rag_dir), "rag-documents.txt")
        rag_docs_file.write_text(rag_files)

        return True

    @classmethod
    def del_rag(cls, path_name: AnyPath, rag_dir: AnyPath = RAG_EXT_DIR) -> bool:
        """Delete RAG documents from the specified RAG directory.
        :param path_name: The path of the RAG documents to delete.
        :param rag_dir: The directory where RAG documents will be deleted from.
        :return: True if the deletion operation was successful, False otherwise.
        """
        src_path: PathObject = PathObject.of(f"{rag_dir}/{path_name}")
        if src_path.exists:
            if src_path.is_file:
                ret_val = safe_delete_file(src_path.abs_dir)
            else:
                shutil.rmtree(src_path.abs_dir)
                ret_val = True
        else:
            return False

        if ret_val:
            files: list[str] = sorted(glob.glob(f"{str(rag_dir)}/**/*.*", recursive=True))
            rag_files: str = "".join(list(ensure_endswith(d, os.linesep) for d in files))
            rag_docs_file: Path = Path(os.path.join(rag_dir), "rag-documents.txt")
            rag_docs_file.write_text(rag_files)

        return ret_val

    @classmethod
    def clear(cls, rag_dir: AnyPath = RAG_EXT_DIR) -> bool:
        """Wipe RAG documents from the specified RAG directory.
        :param rag_dir: The directory where RAG documents will be deleted from.
        :return: True if the deletion operation was successful, False otherwise.
        """
        try:
            src_path: PathObject = PathObject.of(rag_dir)
            shutil.rmtree(src_path.abs_dir)
            os.makedirs(src_path.abs_dir)
            return True
        except OSError:
            return False

    @staticmethod
    def requires_update(rag_dir: AnyPath = RAG_EXT_DIR) -> bool:
        """Check whether the RAG directory has changed and therefore, requires an update from the Chroma DB.
        :return: True if an update is required, False otherwise
        """
        rag_docs_file: Path = Path(os.path.join(rag_dir), "rag-documents.txt")
        rag_hash_file: Path = Path(os.path.join(dirname(str(rag_docs_file)), ".rag-hash"))
        files_hash: str = hash_text(Path(rag_docs_file).read_text())
        if not os.path.exists(str(rag_docs_file)) or not os.path.exists(str(rag_hash_file)):
            rag_hash_file.write_text(files_hash)
            return True
        rag_hash: str = rag_hash_file.read_text()
        rag_hash_file.write_text(files_hash)
        return files_hash != rag_hash

    def __init__(self, rag_filepath: str):
        self._rag_db = None
        self._rag_path: str = os.path.join(str(self.RAG_DIR), rag_filepath)
        self._rag_docs: list[Document] = load_csv(self._rag_path)
        self._rag_db: VectorIndex | None = None
        check_state(file_is_not_empty(self._rag_path))

    def get_rag_examples(self, query: str, k: int = configs.rag_retrival_amount) -> Optional[str]:
        """Retrieve a list of relevant examples based on the provided query.
        :param query: The search query used to retrieve examples.
        :param k: The number of examples to retrieve (default is 3).
        :return: A list of strings representing the retrieved examples.
        """
        if configs.is_rag:
            if self._rag_db is None:
                from askai.core.support.shared_instances import shared
                self._rag_db = VectorIndex(shared.engine.embed)
                self._rag_db.replace(self._rag_docs)
            example_docs: list[Document] = self._rag_db.search(query, k=k)
            rag_examples: list[str] = [doc.page_content for doc in example_docs]
            return f'**Examples:**\n"""{(2 * os.linesep).join(rag_examples)}"""'

        return None
