#!/usr/bin/env python

# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import itertools
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from pre_commit.clientlib import load_config
from pre_commit.constants import CONFIG_FILE


class Hook:
    def __init__(self, id: str, exclude_paths: list[Path]) -> None:
        self.__id = id
        self.__exclude_paths = exclude_paths

    @classmethod
    def from_hook_config(cls: type[Hook], root_directory: Path, hook_config: dict[str, str]) -> Hook:
        exclude_list = (
            hook_config["exclude"]
            .replace("\n", "")
            .replace(" ", "")
            .replace("(?x)^(", "")
            .replace("^", "")
            .replace(")", "")
            .split("|")
        )

        excluded_paths_list = [
            root_directory / Path(exclude) for exclude in exclude_list if not is_regex_pattern(exclude)
        ]

        return cls(hook_config["id"], excluded_paths_list)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def exclude_paths(self) -> list[Path]:
        return self.__exclude_paths

    def find_duplicates(self) -> list[Path]:
        counter = Counter(self.exclude_paths)

        return [path for path in counter if counter[path] > 1]

    def find_non_existing_paths(self) -> list[Path]:
        return [path for path in self.exclude_paths if not path.resolve().exists()]

    def has_duplicates(self) -> bool:
        return bool(self.find_duplicates())

    def has_non_existing_paths(self) -> bool:
        return bool(self.find_non_existing_paths())

    def count_excluded_files(self) -> int:
        existing_paths = [path for path in self.exclude_paths if path.exists()]
        total_file_count = sum(1 for path in existing_paths if path.is_file())
        excluded_dirs = [path for path in existing_paths if path.is_dir()]
        total_dir_count = sum(
            sum(1 for file in excluded_dir.rglob("*") if file.is_file()) for excluded_dir in excluded_dirs
        )
        return total_file_count + total_dir_count


def is_regex_pattern(exclude: str) -> bool:
    return any(regex_key in exclude for regex_key in ["*", "$", "^"])


def has_excludes(hook_config: dict[str, str]) -> bool:
    return bool(hook_config.get("exclude")) and hook_config.get("exclude") != "^$"


def load_hooks(root_directory: Path, config_file: Path) -> list[Hook]:
    config = load_config(config_file)
    hook_configs = itertools.chain(*[repo["hooks"] for repo in config["repos"]])

    return [Hook.from_hook_config(root_directory, hook) for hook in hook_configs if has_excludes(hook)]


def have_non_existent_paths_or_duplicates(hooks_list: list[Any]) -> bool:
    non_existing_paths: list[tuple[str, str]] = [
        (hook_instance.id, path)
        for hook_instance in hooks_list
        if hook_instance.has_non_existing_paths()
        for path in hook_instance.find_non_existing_paths()
    ]
    duplicates: list[tuple[str, str]] = [
        (hook_instance.id, duplicate)
        for hook_instance in hooks_list
        if hook_instance.has_duplicates()
        for duplicate in hook_instance.find_duplicates()
    ]

    if non_existing_paths:
        print(f"Remove the following non-existing exclusions in {CONFIG_FILE}:")
        for hook_id, path in non_existing_paths:
            print(f"In hook {hook_id}: {str(path).split('Repo/', 1)[-1]}")

    if duplicates:
        print(f"Remove the following duplicates from the exclusions in {CONFIG_FILE}:")
        for hook_id, duplicate in duplicates:
            print(f"In hook {hook_id}: {str(duplicate).split('Repo/', 1)[-1]}")

    return bool(non_existing_paths or duplicates)


def print_excluded_files_report(hooks_list: list[Any]) -> None:
    hooks_with_excluded_files = [
        {"hook_id": hook.id, "excluded_files_count": hook.count_excluded_files()}
        for hook in hooks_list
        if hook.count_excluded_files() > 0
    ]
    output_data = {
        "total_excluded_files": sum(hook["excluded_files_count"] for hook in hooks_with_excluded_files),
        "hooks": hooks_with_excluded_files,
    }
    print(json.dumps(output_data, indent=2))


def main() -> int:
    repo_root = Path.cwd()
    pre_commit_config = repo_root / CONFIG_FILE
    hooks_list = load_hooks(repo_root, pre_commit_config)
    print_excluded_files_report(hooks_list)
    return 1 if have_non_existent_paths_or_duplicates(hooks_list) else 0


if __name__ == "__main__":
    sys.exit(main())
