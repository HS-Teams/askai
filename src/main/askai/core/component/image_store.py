#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.components
   @file: recorder.py
@created: Wed, 22 Feb 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from askai.core.router.tools.vision import offline_captioner
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from collections import namedtuple
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from hashlib import sha256

from os.path import basename
from pathlib import Path
from torchvision.datasets.folder import is_image_file
from typing import Any, Mapping, Optional, TypeAlias

import askai.core.component.cache_service as cache
import chromadb
import logging as log
import numpy
import os

def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


Metadata: TypeAlias = Mapping[str, str | int | float | bool]

ImageData: TypeAlias = numpy.ndarray[Any, numpy.dtype]

ImageFile = namedtuple("ImageFile", ["img_id", "img_path", "img_category", "img_caption"])

ImageMetadata = namedtuple("ImageMetadata", ["caption", "data", "uri", "distance"])


class ImageStore(metaclass=Singleton):
    """Provide an interface to store, retrieve, locate, and vectorize images. This class manages the storage and
    retrieval of images, as well as their localization and vectorization for various applications.
    """

    INSTANCE: "ImageStore"

    # fmt: off

    COLLECTION_NAME: str    = "image_store"

    PHOTO_CATEGORY: str     = "photos"

    FACE_CATEGORY: str      = "faces"

    IMPORTS_CATEGORY: str   = "imports"

    # fmt: on

    @staticmethod
    def sync_folders(with_caption: bool = False, *dirs: AnyPath) -> list[ImageFile]:
        """Load image files from the specified directories."""

        def category() -> str:
            """Determine and return the category based on the directory path.
            :return: A string representing the category.
            """
            cat_str: str
            if dir_path == str(cache.PHOTO_DIR):
                cat_str = store.PHOTO_CATEGORY
            elif dir_path == str(cache.FACE_DIR):
                cat_str = store.FACE_CATEGORY
            else:
                cat_str = store.IMPORTS_CATEGORY
            return cat_str

        img_files: list[ImageFile] = []
        load_dirs: list[str] = [str(p) for p in dirs]
        for dir_path, dir_names, file_names in os.walk(cache.PICTURE_DIR):
            if dir_path in load_dirs:
                cat: str = category()
                files: list[str] = list(filter(is_image_file, map(lambda fn: os.path.join(dir_path, fn), file_names)))
                img_files.extend(
                    ImageFile(sha256_text(basename(f)), f, cat, offline_captioner(f) if with_caption else "No caption")
                    for f in files
                )

        return img_files

    def __init__(self):
        self._db_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._img_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME, embedding_function=OpenCLIPEmbeddingFunction(), data_loader=ImageLoader()
        )

    @property
    def persist_dir(self) -> Path:
        return Path.joinpath(cache.PICTURE_DIR, self.COLLECTION_NAME)

    @property
    def metadatas(self) -> Optional[list[Metadata]]:
        return self._img_collection.get()["metadatas"]

    def enlist(self) -> Optional[list[str]]:
        return [str(mt).replace("'", '"') for mt in self.metadatas]

    def store_image(self, *image_files: ImageFile) -> int:
        """Add the provided images to the image store collection.
        :param image_files: One or more ImageFile objects representing the images to be stored.
        :return: The number of images successfully added to the store.
        """

        def _get_caption(caption: str | list | None) -> Optional[str]:
            return os.linesep.join(caption) if isinstance(caption, list) else caption or "Unavailable"

        img_ids: list[str] = list()
        if image_files:
            img_ids.extend([ff.img_id for ff in image_files])
            img_uris = [ff.img_path for ff in image_files]
            img_metas = [
                {
                    "img_id": ff.img_id,
                    "img_path": ff.img_path,
                    "img_category": ff.img_category,
                    "img_caption": _get_caption(ff.img_caption),
                }
                for ff in image_files
            ]
            self._img_collection.add(ids=img_ids, uris=img_uris, metadatas=img_metas)
            log.info("Image collection increased to: '%d' !", self._img_collection.count())

        return len(img_ids)

    def clear_store(self) -> None:
        """Clear the image store collection."""
        log.info("Clearing image store collection: '%s'", self.COLLECTION_NAME)
        self._db_client.delete_collection(self.COLLECTION_NAME)
        self._img_collection = self._db_client.get_or_create_collection(
            self.COLLECTION_NAME, embedding_function=OpenCLIPEmbeddingFunction(), data_loader=ImageLoader()
        )

    def sync_store(self, re_caption: bool = False) -> int:
        """Synchronize the image store collection with the cached pictures folder.
        :param re_caption: Whether to regenerate captions for the images during synchronization (default is False).
        :return: The number of images synchronized with the store.
        """
        log.info(
            "Synchronizing image store folders: '%s', '%s' and '%s'",
            cache.PHOTO_DIR,
            cache.FACE_DIR,
            cache.IMG_IMPORTS_DIR,
        )
        self.clear_store()
        img_files: list[ImageFile] = self.sync_folders(
            re_caption, cache.PHOTO_DIR, cache.FACE_DIR, cache.IMG_IMPORTS_DIR
        )
        self.store_image(*img_files)

        return len(img_files)

    def query_image(self, description: str, k: int = 3) -> list[ImageMetadata]:
        """Query the image store for photos matching the provided description.
        :param description: A text description to match against the stored images.
        :param k: The maximum number of matching results to return (default is 3).
        :return: A list of ImageMetadata objects for the photos that match the description.
        """
        return self.find_by_description(description, [self.PHOTO_CATEGORY, self.IMPORTS_CATEGORY], k)

    def query_face(self, description: str, k: int = 5) -> list[ImageMetadata]:
        """Query the image store for faces matching the provided description.
        :param description: A text description to match against the stored faces.
        :param k: The maximum number of matching faces to return (default is 1).
        :return: A list of ImageMetadata objects for the faces that match the description.
        """
        return self.find_by_description(description, [self.FACE_CATEGORY], k)

    def find_by_description(self, description: str, categories: list[str], k: int = 5) -> list[ImageMetadata]:
        """Find images using natural language.
        :param description: A natural language description to match against stored images.
        :param categories: A list of categories to limit the search within.
        :param k: The maximum number of matching images to return (default is 3).
        :return: A list of ImageMetadata objects for the images that match the description and categories.
        """
        return self._query(k, categories=categories, query_texts=[description])

    def find_by_similarity(self, photo: ImageData, k: int = 5) -> list[ImageMetadata]:
        """Find images that match the provided photo using similarity methods.
        :param photo: The ImageData object representing the photo to match against stored faces.
        :param k: The maximum number of matching faces to return (default is 3).
        :return: A list of ImageMetadata objects for the faces that match the provided photo.
        """
        return self._query(k, categories=[self.FACE_CATEGORY], query_images=[photo])

    def _query(self, k: int = 5, **kwargs) -> list[ImageMetadata]:
        """Query the image store collection for entries that match the provided arguments, sorted by distance.
        :param k: The maximum number of results to return (default is 5).
        :param kwargs: Additional arguments to filter and refine the query, such as categories or other search parameters.
        :return: A list of ImageMetadata objects that match the query, sorted by distance.
        """
        result: list[ImageMetadata] = []
        categories: list[str] = kwargs["categories"] or []
        filters: dict[str, Any] = self._category_filter(categories)
        del kwargs["categories"]
        query_results = self._img_collection.query(
            **kwargs,
            n_results=5,
            include=[
                "documents",
                "distances",
                "metadatas",
                "data",
                "uris",
            ],
            where=filters,
        )
        for i in range(len(query_results["ids"][0])):
            if (img_data := get_or_default(query_results["data"][0], i, None)) is None:
                continue
            img_name = query_results["metadatas"][0][i]["img_caption"]
            img_path = query_results["metadatas"][0][i]["img_path"]
            img_dist = query_results["distances"][0][i]
            result.append(ImageMetadata(img_name, img_data, img_path, img_dist))
        # Sort by distance
        result.sort(key=lambda img: img[3])

        return result[0:k]

    def _category_filter(self, categories: list[str]) -> dict[str, Any]:
        """Build a ChromaDB category filter for querying images.
        :param categories: A list of category names to include in the filter.
        :return: A dictionary representing the category filter to be used in image queries.
        """
        return (
            {"$or": [{"img_category": cat} for cat in categories]}
            if len(categories) > 1
            else {"img_category": get_or_default(categories, 0, "")}
        )


assert (store := ImageStore().INSTANCE) is not None
