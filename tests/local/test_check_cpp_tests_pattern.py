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


def test__hooks_manifest__contains_hook_validating_test_filenames(cpp_tests_name_hook: dict) -> None:
    assert "files" in cpp_tests_name_hook
