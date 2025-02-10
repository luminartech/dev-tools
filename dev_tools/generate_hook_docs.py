#!/usr/bin/env python

# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import re
import sys
from pathlib import Path

from pre_commit.clientlib import load_manifest
from pre_commit.constants import MANIFEST_FILE


def generate_hooks_documentation(hooks: list[dict]) -> str:
    return "\n".join([f"### `{hook['id']}`\n\n{hook['description']}\n" for hook in hooks])


def update_hooks_documentation_in_readme(readme: Path, docs: str) -> None:
    content = readme.read_text()
    content = re.sub(
        r"(<!-- hooks-doc start -->\n)(.*?)(<!-- hooks-doc end -->)",
        rf"\1\n{docs}\3",
        content,
        flags=re.DOTALL,
    )
    readme.write_text(content)


def main() -> int:
    repo_root = Path.cwd()
    readme = repo_root / "README.md"
    hooks_manifest = repo_root / MANIFEST_FILE
    hooks = list(load_manifest(hooks_manifest))
    docs = generate_hooks_documentation(hooks)
    update_hooks_documentation_in_readme(readme, docs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
