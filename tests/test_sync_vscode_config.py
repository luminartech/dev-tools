# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

import re
from pathlib import Path

import pytest

from dev_tools.sync_vscode_config import (
    DictOverwriteRecord,
    combine_lists_without_duplicates,
    load_devcontainer_config,
    update_vscode_extensions_json,
    update_vscode_settings_json,
)


@pytest.fixture
def simple_devcontainer_json() -> str:
    return """
{
  "name": "a devcontainer",
  "customizations": {
    "vscode": {
      "extensions": [
        "BazelBuild.vscode-bazel",
        "GitHub.copilot"
      ],
      "settings": {
        "redhat.telemetry.enabled": false,
        "files.associations": {
          "BUILD.bazel.*": "starlark"
        },
        "python.analysis.exclude": [
          "bazel-bin/**",
          "bazel-out/**"
        ]
      }
    }
  }
}
"""


def read_text_without_whitespace(file_path: Path) -> str:
    return re.subn(r"\s", "", file_path.read_text())[0]


def test__load_devcontainer_config__loads_extensions(tmp_path: Path, simple_devcontainer_json: str) -> None:
    devcontainer_json_path = tmp_path / "devcontainer.json"
    devcontainer_json_path.write_text(simple_devcontainer_json)
    read_config = load_devcontainer_config(devcontainer_json_path)
    assert "BazelBuild.vscode-bazel" in read_config["extensions"]


def test__load_devcontainer_config__loads_settings(tmp_path: Path, simple_devcontainer_json: str) -> None:
    devcontainer_json_path = tmp_path / "devcontainer.json"
    devcontainer_json_path.write_text(simple_devcontainer_json)
    read_config = load_devcontainer_config(devcontainer_json_path)
    assert ("redhat.telemetry.enabled", False) in read_config["settings"].items()


def test__load_devcontainer_config__loads_json_with_comments(tmp_path: Path) -> None:
    devcontainer_json_path = tmp_path / "devcontainer.json"
    devcontainer_json_path.write_text("""
{
  // This is a comment
  "customizations": {
    "vscode": {
      "extensions": [],
      "settings": {}
    }
  }
}
""")
    read_config = load_devcontainer_config(devcontainer_json_path)
    assert "extensions" in read_config


def test__update_vscode_settings_json__creates_new_settings(tmp_path: Path) -> None:
    settings_json_path = tmp_path / "settings.json"
    update_vscode_settings_json(settings_json_path, {"redhat.telemetry.enabled": False})
    assert settings_json_path.exists()
    text_without_whitespace = read_text_without_whitespace(settings_json_path)
    assert text_without_whitespace == '{"redhat.telemetry.enabled":false}'


def test__update_vscode_settings_json__updates_existing_settings(tmp_path: Path) -> None:
    settings_json_path = tmp_path / "settings.json"
    settings_json_path.write_text('{"redhat.telemetry.enabled":true}')

    overwrite_records = update_vscode_settings_json(settings_json_path, {"redhat.telemetry.enabled": False})

    text_without_whitespace = read_text_without_whitespace(settings_json_path)
    assert text_without_whitespace == '{"redhat.telemetry.enabled":false}'
    assert len(overwrite_records) == 1
    assert overwrite_records[0] == DictOverwriteRecord(key="redhat.telemetry.enabled", old_value=True, new_value=False)


def test__update_vscode_settings_json__leaves_custom_settings(tmp_path: Path) -> None:
    settings_json_path = tmp_path / "settings.json"
    settings_json_path.write_text('{"another.setting":5}')

    overwrite_records = update_vscode_settings_json(settings_json_path, {"redhat.telemetry.enabled": False})

    text_without_whitespace = read_text_without_whitespace(settings_json_path)
    assert '"another.setting":5' in text_without_whitespace
    assert '"redhat.telemetry.enabled":false' in text_without_whitespace
    assert overwrite_records == []


def test__update_vscode_settings_json__formats_the_json(tmp_path: Path) -> None:
    settings_json_path = tmp_path / "settings.json"

    settings = {
        "setting1": 1,
        "setting2": 2,
    }
    update_vscode_settings_json(settings_json_path, settings)

    lines = settings_json_path.read_text().splitlines()
    setting1_lines = [n for n, line in enumerate(lines) if "setting1" in line]
    setting2_lines = [n for n, line in enumerate(lines) if "setting2" in line]

    assert len(setting1_lines) == 1
    assert len(setting2_lines) == 1
    assert setting1_lines != setting2_lines


def test__update_vscode_settings_json__adds_newline_at_the_end(tmp_path: Path) -> None:
    settings_json_path = tmp_path / "settings.json"
    update_vscode_settings_json(settings_json_path, {"setting1": 1})

    text = settings_json_path.read_text()
    assert text.endswith("\n")


def test__update_vscode_extensions_json__creates_new_recommendations(tmp_path: Path) -> None:
    extensions_json_path = tmp_path / "extensions.json"
    update_vscode_extensions_json(extensions_json_path, ["charliermarsh.ruff"])
    assert extensions_json_path.exists()
    text_without_whitespace = read_text_without_whitespace(extensions_json_path)
    assert re.search("recommendations.*charliermarsh.ruff", text_without_whitespace)


def test__update_vscode_extensions_json__adds_new_recommendations(tmp_path: Path) -> None:
    extensions_json_path = tmp_path / "extensions.json"
    extensions_json_path.write_text('{"recommendations":["charliermarsh.ruff"]}')

    update_vscode_extensions_json(extensions_json_path, ["ms-python.python"])

    text_without_whitespace = read_text_without_whitespace(extensions_json_path)
    assert re.search("recommendations.*charliermarsh.ruff", text_without_whitespace)
    assert re.search("recommendations.*ms-python.python", text_without_whitespace)


def test__update_vscode_extensions_json__makes_recommendations_unique(tmp_path: Path) -> None:
    extensions_json_path = tmp_path / "extensions.json"
    extensions_json_path.write_text('{"recommendations":["charliermarsh.ruff"]}')

    update_vscode_extensions_json(extensions_json_path, ["charliermarsh.ruff"])

    text_without_whitespace = read_text_without_whitespace(extensions_json_path)
    assert len(re.findall("charliermarsh.ruff", text_without_whitespace)) == 1


def test__update_vscode_extensions_json__supports_utf8_chars(tmp_path: Path) -> None:
    extensions_json_path = tmp_path / "extensions.json"
    update_vscode_extensions_json(extensions_json_path, ["🐍"])

    text_without_whitespace = read_text_without_whitespace(extensions_json_path)
    assert "🐍" in text_without_whitespace


def test__update_vscode_extensions_json__adds_newline_at_the_end(tmp_path: Path) -> None:
    extensions_json_path = tmp_path / "extensions.json"
    update_vscode_extensions_json(extensions_json_path, ["ms-python.python"])

    text = extensions_json_path.read_text()
    assert text.endswith("\n")


def test__combine_lists_without_duplicates__combines_disjoint_lists() -> None:
    list1 = ["a", "b", "c"]
    list2 = ["d", "e", "f"]
    combined = combine_lists_without_duplicates(list1, list2)
    assert all(item in combined for item in "abcdef")


def test__combine_lists_without_duplicates__combines_overlapping_lists() -> None:
    list1 = ["a", "b", "c"]
    list2 = ["b", "c", "d"]
    combined = combine_lists_without_duplicates(list1, list2)
    expected_items = {"a", "b", "c", "d"}
    assert all(item in combined for item in expected_items)
    assert len(combined) == len(expected_items)
