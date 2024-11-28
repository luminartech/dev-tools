# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_tools.local.generate_hook_docs import generate_hooks_documentation, update_hooks_documentation_in_readme

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


def test_generate_hooks_documentation__no_hooks__should_be_empty_string() -> None:
    assert generate_hooks_documentation([]) == ""


def test_generate_hooks_documentation__two_hooks__should_be_two_md_sections() -> None:
    hooks = [{"id": "hook1", "description": "Hook 1 description"}, {"id": "hook2", "description": "Hook 2 description"}]
    result = generate_hooks_documentation(hooks)

    assert "### `hook1`" in result
    assert "### `hook2`" in result
    assert "Hook 1 description" in result
    assert "Hook 2 description" in result


def test_update_hooks_documentation_in_readme__valid_markers__should_update_readme(fs: FakeFilesystem) -> None:
    readme = Path("README.md")
    fs.create_file(
        readme,
        contents="# Main title\n\n<!-- hooks-doc start -->\nshould be gone\n<!-- hooks-doc end -->\n## Other subtitle",
    )

    update_hooks_documentation_in_readme(readme, "### `my-hook`\n\nMy hook description")

    content = readme.read_text()
    assert "### `my-hook`\n\nMy hook description" in content, "Should have the new hooks documentation"
    assert "<!-- hooks-doc start -->" in content, "Should still have the start marker"
    assert "<!-- hooks-doc end -->" in content, "Should still have the end marker"
    assert "should be gone" not in content, "Should not have the old hooks documentation"


def test_update_hooks_documentation_in_readme__no_markers__should_not_update_readme(fs: FakeFilesystem) -> None:
    readme = Path("README.md")
    content = "# Main title\n\n## Other subtitle"
    fs.create_file(readme, contents=content)

    update_hooks_documentation_in_readme(readme, "### `my-hook`\n\nMy hook description")

    assert readme.read_text() == content
