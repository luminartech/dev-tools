#!/usr/bin/env python

# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import json  # for writing JSON, we need a pretty printer. PyJSON5 doesn't support this: https://github.com/Kijewski/pyjson5/issues/19#issuecomment-970504400
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyjson5  # for parsing comments, we need JSON5


def load_devcontainer_config(devcontainer_json_path: Path) -> Any:  # noqa: ANN401
    return pyjson5.loads(devcontainer_json_path.read_text())["customizations"]["vscode"]


def get_and_set(dict: Any, key: Any, value: Any) -> Any:  # noqa: ANN401
    old_value = dict.get(key, None)
    dict[key] = value
    return old_value


@dataclass
class DictOverwriteRecord:
    key: str
    old_value: Any
    new_value: Any


@dataclass
class ListOverwriteRecord:
    old_value: Any
    new_value: Any


def update_dict_overwriting_values(dict: Any, new_values_dict: dict) -> list[DictOverwriteRecord]:  # noqa: ANN401
    overwrite_records = []
    for key, value in new_values_dict.items():
        old_value = get_and_set(dict, key, value)
        if old_value is not None and old_value != value:
            overwrite_records.append(DictOverwriteRecord(key, old_value, value))
    return overwrite_records


def combine_lists_without_duplicates(the_list: Any, new_values_list: list) -> list[str]:  # noqa: ANN401
    return sorted(set(the_list) | set(new_values_list))


def update_vscode_settings_json(settings_json: Path, settings_dict: dict) -> list[DictOverwriteRecord]:
    old_settings_dict = pyjson5.loads(settings_json.read_text()) if settings_json.is_file() else {}
    overwrite_records = update_dict_overwriting_values(old_settings_dict, settings_dict)
    settings_json.write_text(json.dumps(old_settings_dict, indent=4, ensure_ascii=False))
    return overwrite_records


def update_vscode_extensions_json(extensions_json: Path, extensions_list: list[str]) -> list[ListOverwriteRecord]:
    old_extensions_dict = pyjson5.loads(extensions_json.read_text()) if extensions_json.is_file() else {}
    old_extensions_list = old_extensions_dict.get("recommendations", [])
    old_extensions_dict["recommendations"] = combine_lists_without_duplicates(old_extensions_list, extensions_list)
    extensions_json.write_text(json.dumps(old_extensions_dict, indent=4, ensure_ascii=False))
    return []


def main() -> int:
    # print warnings for overwrites
    repo_root = Path.cwd()
    devcontainer_json = repo_root / ".devcontainer" / "devcontainer.json"
    vs_code_folder = repo_root / ".vscode"

    devcontainer_config = load_devcontainer_config(devcontainer_json)
    update_vscode_settings_json(vs_code_folder / "settings.json", devcontainer_config["settings"])
    update_vscode_extensions_json(vs_code_folder / "extensions.json", devcontainer_config["extensions"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
