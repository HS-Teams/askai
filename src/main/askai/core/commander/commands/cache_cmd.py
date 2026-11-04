#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.cache_cmd
      @file: cache_cmd.py
   @created: Thu, 27 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from abc import ABC
from askai.core.askai_configs import configs
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.cli import output as cli_output
from functools import partial
from hspylib.core.tools.commons import human_readable_bytes, sysout
from hspylib.core.tools.text_tools import elide_text
from pathlib import Path
from typing import Optional

import os


class CacheCmd(ABC):
    """Provides cache command functionalities."""

    @staticmethod
    def list() -> None:
        """List all cache entries."""
        if not configs.is_cache:
            sysout(f"\n%ORANGE%-=- Cache is disabled! -=-%NC%\n")
        elif (all_keys := sorted(cache.keys)) and (length := len(all_keys)) > 0:
            cli_output.render_message(f"### Listing ALL ({length}) Cached Questions:\n\n---\n\n")
            entries: str = ""
            for i, query in enumerate(all_keys, start=1):
                answer: str | None = cache.read_reply(query)
                if not answer:
                    continue
                cache_str: str = elide_text(answer, 80).replace(os.linesep, "␊")
                entries += f"{i}. **{query}**: `{cache_str}` \n"
            cli_output.render_message(entries)
        else:
            sysout(f"\n%RED%-=- Caching is empty! -=-%NC%")
        cli_output.render_message("\n> Hint: Type: '/cache [get|clear|files|enable|ttl] <args>'.")

    @staticmethod
    def get(name: str) -> Optional[str]:
        """Retrieve a cache entry by its name.
        :param name: The name of the cache entry to retrieve.
        :return: The value of the cache entry as a string, or None if the entry does not exist.
        """
        entry: str = cache.read_reply(name)
        return (
            f'%GREEN%{name}%NC% cache(s) is %CYAN%"{entry}"%NC%'
            if entry
            else f"%YELLOW%'{name}'%NC% was not found in the cache!"
        )

    @staticmethod
    def clear(entry: str | int | None = None) -> None:
        """Clear a specified cache entry or all cache entries.
        :param entry: The cache entry to clear, specified by name or index. If None, all cache entries will be cleared.
        """
        deleted: str | None = None
        if entry:
            if isinstance(entry, int):
                if name := sorted(cache.keys)[entry]:
                    deleted = cache.del_reply(name)
            elif isinstance(entry, str):
                if name := next((obj for obj in cache.keys if obj == entry), None):
                    deleted = cache.del_reply(name)
        else:
            deleted = str(cache.clear_replies())
        cli_output.render_command(f"*{deleted if deleted else 'No'}* cache(s) has been cleared!")

    @staticmethod
    def files(cleanup: bool = False, *args: str | int) -> None:
        """List all cached files from the AskAI cache directory.
        :param cleanup: If True, clean up the listed cache files after displaying them (default is False).
        :param args: Specific file names or indices to target for listing or cleanup.
        """
        if os.path.exists(CACHE_DIR):
            if cleanup:
                for arg in args[1 if cleanup else 0 :]:
                    i_files = Path(f"{CACHE_DIR}").glob(f"{arg}*")
                    while (cached := next(i_files, None)) and os.path.exists(cached):
                        f_join = partial(os.path.join, f"{CACHE_DIR}/{arg}")
                        if os.path.isdir(cached):
                            set(map(os.remove, map(f_join, os.listdir(cached))))
                            cli_output.render_command(f"Folder *{cached}* has been cleared!")
                        elif os.path.isfile(cached):
                            os.remove(cached)
                            cli_output.render_command(f"File **{cached}** was removed!")
            else:
                cli_output.render_message(f"### Listing cached files from '{CACHE_DIR}':\n\n---\n\n")
                files, dirs = "", ""
                for cached in os.listdir(CACHE_DIR):
                    f_cached = os.path.join(CACHE_DIR, cached)
                    if os.path.isdir(f_cached):
                        f_join = partial(os.path.join, f"{CACHE_DIR}/{cached}")
                        f_all = list(map(os.path.getsize, map(f_join, os.listdir(f_cached))))
                        size, unit = human_readable_bytes(sum(f_all))
                        dirs += f"- *{cached}* ({len(f_all)} files {size} {unit}) \n"
                    else:
                        size, unit = human_readable_bytes(os.path.getsize(f_cached))
                        files += f"- **{cached}** ({size} {unit})\n"
                cli_output.render_message(f"{dirs}\n{files}")
                cli_output.render_message(f"\n> Hint: Type: '/cache files cleanup [globs ...]' to delete cached files.")
        else:
            sysout(f"\n%RED%-=- Cache dir {CACHE_DIR} does not exist! -=-%NC%\n")
