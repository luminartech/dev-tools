# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

import re
from pathlib import Path

import pytest

from dev_tools.sync_vscode_config import DictOverwriteRecord, load_devcontainer_config, update_vscode_settings_json


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
