import re

import pytest

from dev_tools.pre_commit_utils import get_hooks_manifest


@pytest.fixture
def build_file_extensions_hook() -> dict:
    hook_id = "check-build-file-without-extensions"
    for hook in get_hooks_manifest():
        if hook["id"] == hook_id:
            return hook
    msg = f"{hook_id} not found in hooks manifest"
    raise ValueError(msg)


def test__hook_validating_build_filenames__is_defined_for_files(build_file_extensions_hook: dict) -> None:
    assert "files" in build_file_extensions_hook


@pytest.mark.parametrize(
    "filename",
    [
        "BUILD.bazel",
        "BUILDFILE",
        "MY_BUILD",
        "BUILD.foo",
        "foo.BUILD",
        "FOO_BUILD",
        "some/path/BUILD.bazel",
        "path/to/BUILDFILE",
        "path/to/BUILD.foo",
        "build",
        "BUILD/something",
        "some/path/build",
    ],
)
def test__hook_validating_build_filenames__allows_valid_cases(build_file_extensions_hook: dict, filename: str) -> None:
    deny_files_pattern: str = build_file_extensions_hook["files"]
    assert not re.search(deny_files_pattern, filename), "Valid BUILD filename should not match the deny pattern"


@pytest.mark.parametrize(
    "filename",
    [
        "BUILD",
        "some/path/BUILD",
        "path/to/BUILD",
        "projects/BUILD",
    ],
)
def test__hook_validating_build_filenames__denies_invalid_cases(
    build_file_extensions_hook: dict, filename: str
) -> None:
    deny_files_pattern: str = build_file_extensions_hook["files"]
    pattern_matches = re.search(deny_files_pattern, filename)
    assert pattern_matches, f"Invalid BUILD filename '{filename}' should match the deny pattern '{deny_files_pattern}'"
