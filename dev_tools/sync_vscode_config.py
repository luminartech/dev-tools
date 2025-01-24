#!/usr/bin/env python

# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_devcontainer_config(devcontainer_json_path: Path) -> dict:
    return json.loads(devcontainer_json_path.read_text())["customization"]["vscode"]


def update_vscode_config_json(settings_json: Path, settings_config: dict) -> None:
    settings_json.write_text(json.dumps(settings_config))


def main() -> int:
    repo_root = Path.cwd()
    devcontainer_json = repo_root / ".devcontainer" / "devcontainer.json"
    vs_code_folder = repo_root / ".vscode"

    devcontainer_config = load_devcontainer_config(devcontainer_json)
    update_vscode_config_json(vs_code_folder / "settings.json", devcontainer_config["settings"])
    update_vscode_config_json(vs_code_folder / "extensions.json", devcontainer_config["extensions"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
