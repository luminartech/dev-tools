# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

import pytest

from dev_tools.sync_vscode_config import load_devcontainer_config


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
