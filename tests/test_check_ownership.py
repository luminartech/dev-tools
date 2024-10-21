# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dev_tools.check_ownership import (
    ReturnCode,
    check_for_files_without_team_ownership,
    check_if_all_codeowners_folders_exist,
    check_if_codeowners_has_ineffective_rules,
    perform_all_codeowners_checks,
)
from dev_tools.ownership_utils import OwnerShipEntry


@pytest.fixture
def repo_dir() -> Path:
    return Path("/test_repo")


@pytest.fixture
def codeowners(repo_dir: Path) -> Path:
    return repo_dir / ".github" / "CODEOWNERS"


@pytest.mark.parametrize(
    ("pattern", "file_path"),
    [("/.gitlab-ci.yml", ".gitlab-ci.yml"), ("test_*.c", "src/test_a.c"), ("/test_*.c", "test_a.c")],
)
def test__check_if_all_codeowners_folders_exist__for_valid_file__should_pass(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path, pattern: str, file_path: Path
) -> None:
    ownership_entries = [
        OwnerShipEntry("/.github", ("@myorg/bar",), 1),
        OwnerShipEntry(pattern, ("@myorg/bar",), 2),
    ]

    fs.create_file(codeowners)
    fs.create_file(repo_dir / file_path)

    assert check_if_all_codeowners_folders_exist(repo_dir, ownership_entries) == ReturnCode.SUCCESS


@pytest.mark.parametrize(
    ("pattern", "file_path"),
    [("/docs/foo*.md", "docs/bar.md"), ("/test_*.c", "src/test_a.c")],
)
def test__check_if_all_codeowners_folders_exist__for_unmatched_pattern__should_fail(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path, pattern: str, file_path: Path
) -> None:
    ownership_entries = [OwnerShipEntry(pattern, ("@myorg/foo_group",), 1)]
    fs.create_file(codeowners)
    fs.create_file(repo_dir / file_path)

    assert check_if_all_codeowners_folders_exist(repo_dir, ownership_entries) == ReturnCode.ERROR_FOLDER_DOESNT_EXIST


def test__check_if_all_codeowners_folders_exist__for_matched_pattern__should_pass(
    fs: FakeFilesystem, repo_dir: Path
) -> None:
    ownership_entries = [OwnerShipEntry("/docs/foo*.md", ("@myorg/foo_group",), 1)]
    fs.create_file(repo_dir / "docs/foo_instructions.md")

    assert check_if_all_codeowners_folders_exist(repo_dir, ownership_entries) == ReturnCode.SUCCESS


def test__check_if_all_codeowners_folders_exist__for_nonexisting_entry__should_fail(repo_dir: Path) -> None:
    ownership_entries = [OwnerShipEntry("/.gitlab-ci.yml", ("@myorg/bar",), 1)]

    assert check_if_all_codeowners_folders_exist(repo_dir, ownership_entries) == ReturnCode.ERROR_FOLDER_DOESNT_EXIST


def test__check_if_codeowners_has_ineffective_rules__for_full_duplicate__should_fail() -> None:
    ownership_entries = [
        OwnerShipEntry("/.gitlab-ci.yml", ("@myorg/bar",), 1),
        OwnerShipEntry("/.gitlab-ci.yml", ("@myorg/bar",), 2),
    ]

    assert check_if_codeowners_has_ineffective_rules(ownership_entries) == ReturnCode.ERROR_DUPLICATE_LINES


def test__check_if_codeowners_has_ineffective_rules__for_pattern_duplicate__should_fail() -> None:
    ownership_entries = [
        OwnerShipEntry("/.gitlab-ci.yml", ("@myorg/bar",), 1),
        OwnerShipEntry("/.gitlab-ci.yml", ("@myorg/anotherteam",), 2),
    ]

    assert check_if_codeowners_has_ineffective_rules(ownership_entries) == ReturnCode.ERROR_MULTIPLE_FOLDER_OWNERS


def test__check_if_codeowners_has_ineffective_rules__for_subfolder_and_parent_folder__should_fail() -> None:
    ownership_entries = [
        OwnerShipEntry("/path/team/subfolder/package_*", ("@myorg/team",), 1),
        OwnerShipEntry("/path/team", ("@myorg/team",), 2),
    ]
    assert check_if_codeowners_has_ineffective_rules(ownership_entries) == ReturnCode.ERROR_RULE_IS_INEFFECTIVE


def test__check_if_codeowners_has_ineffective_rules__for_folder_and_subfolder__should_fail() -> None:
    ownership_entries = [
        OwnerShipEntry("/path/team", ("@myorg/team",), 1),
        OwnerShipEntry("/path/team/subfolder/package_*", ("@myorg/team",), 2),
    ]
    assert check_if_codeowners_has_ineffective_rules(ownership_entries) == ReturnCode.ERROR_RULE_IS_INEFFECTIVE


def test__check_if_codeowners_has_ineffective_rules__for_subfolder_with_different_owner__should_pass() -> None:
    ownership_entries = [
        OwnerShipEntry("/path/team", ("@myorg/team",), 1),
        OwnerShipEntry("/path/team/subfolder/package_*", ("@myorg/bar",), 2),
    ]
    assert check_if_codeowners_has_ineffective_rules(ownership_entries) == ReturnCode.SUCCESS


def test__check_if_codeowners_has_ineffective_rules__for_failing_rule_overridden_by_good_rule__should_fail() -> None:
    ownership_entries = [
        OwnerShipEntry("/path/team", ("@myorg/team",), 1),
        OwnerShipEntry("/path/team/subfolder/package_*", ("@myorg/team",), 2),
        OwnerShipEntry("/path/team/subfolder/package_*", ("@myorg/bar",), 3),
    ]
    assert check_if_codeowners_has_ineffective_rules(ownership_entries) != ReturnCode.SUCCESS


def test_check_for_files_without_team_ownership__only_codeowners_owned_by_codeowners_owner__should_return_success(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    foo_file = repo_dir / ".github" / "foo"
    monkeypatch.setattr("dev_tools.check_ownership.get_git_tracked_files", lambda _: [codeowners, foo_file])

    fs.create_file(
        codeowners,
        contents="""
/.github @myorg/bar
/.github/CODEOWNERS @myorg/codeowners-owner
""",
    )
    fs.create_file(foo_file)

    assert (
        check_for_files_without_team_ownership(repo_dir, [codeowners, foo_file], "@myorg/codeowners-owner", codeowners)
        == ReturnCode.SUCCESS
    )


def test_check_for_files_without_team_ownership__no_codeowners_owner_provided__should_return_success(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    foo_file = repo_dir / ".github" / "foo"
    monkeypatch.setattr("dev_tools.check_ownership.get_git_tracked_files", lambda _: [codeowners, foo_file])

    fs.create_file(codeowners)
    fs.create_file(foo_file)

    assert check_for_files_without_team_ownership(repo_dir, [codeowners, foo_file], None, codeowners) == ReturnCode.SUCCESS


@pytest.mark.parametrize(
    "codeowners_file",
    [Path("/test_repo") / ".github" / "CODEOWNERS", Path("/test_repo") / "CODEOWNERS"],
)
def test_check_for_files_without_team_ownership__file_owned_by_codeowners_owner__should_fail_with_error_file_without_team_ownership(
    fs: FakeFilesystem, repo_dir: Path, monkeypatch: pytest.MonkeyPatch, codeowners_file: Path
) -> None:
    foo_file = repo_dir / ".github" / "foo"
    monkeypatch.setattr("dev_tools.check_ownership.get_git_tracked_files", lambda _: [codeowners_file, foo_file])

    fs.create_file(
        codeowners_file,
        contents="""
* @myorg/codeowners-owner
""",
    )
    fs.create_file(foo_file)

    assert (
        check_for_files_without_team_ownership(repo_dir, [codeowners_file, foo_file], "@myorg/codeowners-owner", codeowners_file)
        == ReturnCode.ERROR_FILE_WITHOUT_TEAM_OWNERSHIP
    )

def test_check_for_files_without_team_ownership__codeowners_changes_but_not_the_file__should_fail_with_error_file_without_team_ownership(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    foo_file = repo_dir / ".github" / "foo"
    monkeypatch.setattr("dev_tools.check_ownership.get_git_tracked_files", lambda _: [codeowners, foo_file])
    fs.create_file(
        codeowners,
        contents="""
* @myorg/codeowners-owner
""",
    )
    fs.create_file(foo_file)
    assert (
        check_for_files_without_team_ownership(repo_dir, [codeowners], "@myorg/codeowners-owner", codeowners)
        == ReturnCode.ERROR_FILE_WITHOUT_TEAM_OWNERSHIP
    )


@pytest.mark.parametrize(
    ("codeowners_path", "file_path"),
    [
        ("/.gitlab-ci.yml @myorg/bar", ".gitlab-ci.yml"),
        ("/.gitlab* @myorg/bar", ".gitlab-ci.yml"),
        ("test_*.c @myorg/test-team", "src/test_a.c"),
        ("/test_*.c @myorg/test-team", "test_a.c"),
    ],
)
def test__perform_all_codeowners_checks__for_valid_file__should_pass(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path, codeowners_path: Path, file_path: Path
) -> None:
    fs.create_file(
        codeowners,
        contents=f"""
/.github @myorg/bar
{codeowners_path}
""",
    )
    fs.create_file(repo_dir / file_path)

    assert perform_all_codeowners_checks(repo_dir, codeowners) == ReturnCode.SUCCESS


def test__perform_all_codeowners_checks__for_single_problem__should_fail_with_error_folder_doenst_exist(
    fs: FakeFilesystem, repo_dir: Path, codeowners: Path
) -> None:
    fs.create_file(
        codeowners,
        contents="""
"/test_*.c @myorg/test-team"
        """,
    )
    fs.create_file(repo_dir / "src/test_a.c")

    return_code = perform_all_codeowners_checks(repo_dir, codeowners)
    assert return_code != ReturnCode.ERROR_MULTIPLE_FOLDER_OWNERS
    assert return_code != ReturnCode.ERROR_RULE_IS_INEFFECTIVE
    assert return_code == ReturnCode.ERROR_FOLDER_DOESNT_EXIST


@pytest.mark.parametrize(
    "codeowners_file",
    [Path("/test_repo") / ".github" / "CODEOWNERS", Path("/test_repo") / "CODEOWNERS"],
)
def test__perform_all_codeowners_checks__for_multiple_problems__should_fail_with_combined_error(
    fs: FakeFilesystem, repo_dir: Path, codeowners_file: Path
) -> None:
    fs.create_file(
        codeowners_file,
        contents="""
/.gitlab-ci.yml @myorg/bar
/.gitlab-ci.yml @myorg/anotherteam
/.gitlab-ci.yml/was_actually_a_folder @myorg/anotherteam
        """,
    )

    return_code = perform_all_codeowners_checks(repo_dir, codeowners_file)
    assert (
        return_code
        == ReturnCode.ERROR_MULTIPLE_FOLDER_OWNERS
        + ReturnCode.ERROR_FOLDER_DOESNT_EXIST
        + ReturnCode.ERROR_RULE_IS_INEFFECTIVE
    )
