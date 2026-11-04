#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.support.utilities
   @file: utilities.py
@created: Wed, 10 Jan 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""

from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith, strip_escapes
from hspylib.core.zoned_datetime import now_ms
from os.path import basename, dirname
from pathlib import Path
from typing import Optional, TypeAlias

import base64
import mimetypes
import os
import re
import shlex
import shutil
import sys

QueryString: TypeAlias = None | str | list[str]


def read_stdin() -> Optional[str]:
    """Read input from the standard input (stdin).
    :return: The input read from stdin as a string, or None if no input is provided.
    """
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def find_file(filename: AnyPath) -> Optional[Path]:
    """Find the specified file by name in the most common locations.
    :param filename: The name or path of the file to find.
    :return: The full path to the file if found, otherwise None.
    """
    prompt_path: Path | None = Path(filename) if filename else None
    if prompt_path and not prompt_path.exists():
        prompt_path = Path(os.path.expandvars(os.path.expanduser(str(filename))))
        if not prompt_path.exists():
            prompt_path = Path(os.path.join(os.getcwd(), str(filename)))
            if not prompt_path.exists():
                prompt_path = Path(os.path.join(Path.home(), str(filename)))
    return prompt_path if prompt_path and prompt_path.exists() else None


def copy_file(srcfile: AnyPath | Path, destfile: AnyPath | Path) -> str:
    """Copy the specified file to the given destination path.
    :param srcfile: The path of the source file to be copied.
    :param destfile: The destination path where the file should be copied.
    :return: The path of the copied file as a string.
    """
    filepath: PathObject | None = PathObject.of(srcfile)
    dest_dir: PathObject | None = PathObject.of(destfile)
    check_argument(
        filepath is not None
        and filepath.exists
        and filepath.is_file
        and dest_dir is not None
        and dest_dir.exists
        and dest_dir.is_dir
    )
    dest_file: str = os.path.join(dest_dir.abs_dir, filepath.filename)
    shutil.copy(str(srcfile), str(dest_file))
    return dest_file


def build_img_path(base_dir: Path, filename: str, suffix: str) -> Optional[str]:
    """Construct the full path for an image file based on the base directory, filename, and suffix.
    :param base_dir: The base directory where the image file is located.
    :param filename: The name of the image file (without the suffix).
    :param suffix: The suffix or extension to append to the filename (e.g., ".jpg", ".png").
    :return: The full path to the image file as a string, or None if the path cannot be constructed.
    """
    if not filename:
        return None
    img_path: str = str(Path.joinpath(base_dir, basename(filename or f"ASKAI-{now_ms()}"))).strip()
    img_path = re.sub(r"\s+", "-", ensure_endswith(img_path, suffix))
    img_path = re.sub(r"-+", "-", img_path)
    return strip_escapes(img_path)


def join_path(dir_name: AnyPath, path_name: AnyPath) -> str:
    """Join the the given path name with the specified directory name.
    :param dir_name: The new directory name to replace the existing one.
    :param path_name: The original path where the directory will be replaced.
    :return: The modified path with the new directory name.
    """

    return os.path.join(str(dir_name), str(path_name))


def read_resource(base_dir: AnyPath, filename: AnyPath, file_ext: str = ".txt") -> str:
    """Read the resource file specified by the filename and return its content.
    :param base_dir: The base directory, relative to the resources folder.
    :param filename: The name of the file to read.
    :param file_ext: The file extension of the file (default is ".txt").
    :return: The content of the file as a string.
    """
    _, ext = os.path.splitext(str(filename))
    filename = f"{str(base_dir)}/{ensure_endswith(basename(str(filename)), ext or file_ext)}"
    check_argument(file_is_not_empty(str(filename)), f"Resource file is empty or does not exist: {filename}")
    return Path(filename).read_text(encoding=Charset.UTF_8.val)


def read_file(load_dir: AnyPath, path_name: str) -> str:
    """Reads the contents of a file from the specified directory.
    :param load_dir: The directory where the file is located.
    :param path_name: The path name of the file to read.
    :return: The contents of the file as a string, or None if the file cannot be read.
    """
    file: Path | None = find_file(Path(join_path(load_dir, path_name)))
    return file.read_text(encoding=Charset.UTF_8.val) if file and file_is_not_empty(str(file)) else ""


def encode_image(file_path: str):
    """Encode an image file to a base64 string.
    :param file_path: Path to the image file to be encoded.
    :return: Base64 encoded string of the image file.
    """
    with open(file_path, "rb") as f_image:
        return base64.b64encode(f_image.read()).decode(Charset.UTF_8.val)


def extract_path(command_line: str) -> Optional[str]:
    """Extract the first identifiable path from the provided command line text.
    :param command_line: The command line text from which to extract the path.
    :return: The first identified path as a string, or None if no path could be extracted.
    """
    if not (tokens := shlex.split(os.path.expanduser(os.path.expandvars(command_line)))):
        return None
    # Remove the command itself
    tokens = tokens[1:]
    # Remove options (tokens starting with '-')
    args = [arg for arg in tokens if not arg.startswith("-")]
    for arg in args:
        arg = arg.replace("\\ ", " ")  # Replace space escapes
        arg = arg[:-1] if arg.endswith(";") else arg  # Remove semi-colon endings
        if (_path_ := Path(arg)) and _path_.exists() and _path_.is_dir():
            return arg
        elif os.path.exists(dirname(arg)) and os.path.isdir(dirname(arg)):
            return dirname(arg)
    return None


def extract_codeblock(text: str) -> tuple[str | None, str]:
    """Extract the programming language and actual code from a markdown multi-line code block.
    :param text: The markdown-formatted text containing the code block.
    :return: A tuple where the first element is the programming language (or None if not specified),
             and the second element is the extracted code as a string.
    """
    flags: int = re.IGNORECASE | re.MULTILINE | re.DOTALL
    # Match a markdown code block with an optional language specifier
    re_command = r"\s*```([\w+-]*)\s*\n(.*?)\s*\n```\s*"
    if mat := re.search(re_command, text, flags=flags):
        lang = mat.group(1)
        code = mat.group(2)
        return lang.strip() if lang else None, code.strip() if code else ""
    return None, ""


def media_type_of(pathname: str) -> Optional[tuple[str | None, ...]]:
    """Return the media type of the specified file, or None if the type could not be determined.
    :param pathname: The file path to check.
    :return: A tuple representing the media type (e.g., ("text/plain")), or None if guessing was not possible.
    """
    media_type, _ = mimetypes.guess_type(os.path.basename(pathname))
    if media_type:
        return tuple(media_type.split("/"))
    return None


def seconds(millis: int) -> float:
    """Convert milliseconds to seconds.
    :param millis: The time in milliseconds.
    :return: The equivalent time in seconds as a float.
    """
    return millis / 1000
