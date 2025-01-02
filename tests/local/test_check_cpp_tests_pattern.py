import re

import pytest

from dev_tools.pre_commit_utils import get_hooks_manifest


@pytest.fixture
def cpp_tests_name_hook() -> dict:
    hook_id = "check-cpp-and-cu-unit-test-naming-pattern"
    for hook in get_hooks_manifest():
        if hook["id"] == hook_id:
            return hook
    msg = f"{hook_id} not found in hooks manifest"
    raise ValueError(msg)


def test__hook_validating_test_filenames__is_defined_for_files(cpp_tests_name_hook: dict) -> None:
    assert "files" in cpp_tests_name_hook


@pytest.mark.parametrize(
    "filename",
    [
        "src/tests/foo_test.cpp",
        "src/tests/foo_test.cu",
        "src/tests/pythontest.py",
        "src/tests/footest.cpp.txt",
        "src/python_tests/foo.py",
        "src/python_test/foo.py",
    ],
)
def test__hook_validating_test_filenames__allows_valid_cases(cpp_tests_name_hook: dict, filename: str) -> None:
    deny_files_pattern: str = cpp_tests_name_hook["files"]
    assert not re.match(deny_files_pattern, filename)


@pytest.mark.parametrize("filename", ["src/tests/footest.cpp", "src/tests/foo_tests.cpp"])
def test__hook_validating_test_filenames__denies_invalid_cases(cpp_tests_name_hook: dict, filename: str) -> None:
    deny_files_pattern: str = cpp_tests_name_hook["files"]
    assert re.match(deny_files_pattern, filename)
