# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path, PurePath

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dev_tools.ownership_utils import GithubOwnerShip, get_ownership_entries


def _create_repo_path_with_codeowners_file(fs: FakeFilesystem, codeowners_content: str = "") -> Path:
    repo_dir = Path("repo")
    codeowners = repo_dir / ".github" / "CODEOWNERS"
    fs.create_file(codeowners, contents=codeowners_content)
    return repo_dir


def testis_file_covered_by_pattern__matches_file(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert unit.is_file_covered_by_pattern(Path("foo") / "bar" / "file.py", "file.py")
    assert unit.is_file_covered_by_pattern(Path("foo") / "bar" / "file.py", "foo/bar")
    assert unit.is_file_covered_by_pattern(Path("a") / "b" / "c" / "d" / "e.txt", "b/c/d")
    assert unit.is_file_covered_by_pattern(Path("b") / "c" / "d" / "e.txt", "b/c/d")


def testis_file_covered_by_pattern__does_not_match_file(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert not unit.is_file_covered_by_pattern(Path("foo") / "bar" / "src" / "CMakeLists.txt", "file.py")
    assert not unit.is_file_covered_by_pattern(Path("foo") / "bar" / "file.py", "/file.py")
    assert not unit.is_file_covered_by_pattern(Path("b") / "c" / "f" / "unit.cpp", "b/c/d")
    assert not unit.is_file_covered_by_pattern(Path("a") / "b" / "c" / "d" / "e.txt", "/b/c/d")


def testis_file_covered_by_pattern__wildcard_pattern_matches_file(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert unit.is_file_covered_by_pattern(Path("src") / "team_a_setup" / "install.py", "/src/team_a_*")
    assert unit.is_file_covered_by_pattern(
        Path("foo") / "some_specific_aaaa_name" / "src" / "config.yml", "foo/some_*_aaaa_*"
    )
    assert unit.is_file_covered_by_pattern(
        Path("foo") / "some_specific_name_with_more" / "CMakeLists.txt", "foo/some_*_name_*"
    )
    assert unit.is_file_covered_by_pattern(
        Path("src") / "foo" / "some_specific_name_with_more" / "CMakeLists.txt", "foo/some_*_name_*"
    )


def testis_file_covered_by_pattern__match_leading_and_trailing_os_separator(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert unit.is_file_covered_by_pattern(Path("src") / "team_a_setup" / "install.py", "/src/team_a_setup/install.py")
    assert unit.is_file_covered_by_pattern(Path("src") / "team_a_setup" / "install.py", "src/team_a_setup/install.py")
    assert unit.is_file_covered_by_pattern(Path("src") / "team_a_setup", "/src/team_a_setup/")
    assert unit.is_file_covered_by_pattern(Path("src") / "team_a_setup", "src/team_a_setup/")


def testis_file_covered_by_pattern__wildcard_pattern_does_not_match_file(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert not unit.is_file_covered_by_pattern(Path("src") / "team_b_setup" / "install.py", "/src/team_a_*")
    assert not unit.is_file_covered_by_pattern(
        Path("foo") / "some_specific_aaaa_name" / "config.yml", "foo/some_*_bbb_*"
    )
    assert not unit.is_file_covered_by_pattern(
        Path("foo") / "some_specific_name" / "CMakeLists.txt", "foo/some_*_name_*"
    )
    assert not unit.is_file_covered_by_pattern(
        Path("src") / "foo" / "some_aaaaa_name" / "CMakeLists.txt", "foo/some_bbbb_*"
    )


def testis_file_covered_by_pattern__wildcard_for_non_recursive_ownership(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert unit.is_file_covered_by_pattern(Path("src") / "README.md", "src/*")
    assert unit.is_file_covered_by_pattern(Path("src") / "README.md", "/src/*")
    assert not unit.is_file_covered_by_pattern(Path("src") / "packages" / "README.md", "/src/*")
    assert not unit.is_file_covered_by_pattern(Path("src") / "packages" / "README.md", "src/*")

    # Additional asterisk in path
    assert unit.is_file_covered_by_pattern(Path("src") / "packages" / "CMakeLists.txt", "pa*ges/*")
    assert not unit.is_file_covered_by_pattern(Path("src") / "packages" / "CMakeLists.txt", "/pa*ges/*")
    assert unit.is_file_covered_by_pattern(Path("src") / "packages" / "CMakeLists.txt", "/src/pa*ges/*")
    assert not unit.is_file_covered_by_pattern(
        Path("src") / "packages" / "package_a" / "CMakeLists.txt", "/src/pa*ges/*"
    )


def testis_file_covered_by_pattern__almighty_wildcard(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert unit.is_file_covered_by_pattern(Path("CONTRIBUTING.md"), "*")
    assert unit.is_file_covered_by_pattern(Path("src") / "README.md", "*")
    assert unit.is_file_covered_by_pattern(Path("foo") / "bar" / "file.py", "*")


def testis_file_covered_by_pattern__full_path_matches(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(fs)
    unit = GithubOwnerShip(repo_dir)

    assert unit.is_file_covered_by_pattern(Path("foo/bar"), "/foo/bar")
    assert not unit.is_file_covered_by_pattern(Path("foo/other"), "/foo/bar")


def test_github_ownership_is_file_owned_by(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(
        fs,
        codeowners_content="""/foo.txt devs
/docs/ devs management""",
    )
    unit = GithubOwnerShip(repo_dir)
    assert unit.is_owned_by(repo_dir / "foo.txt", "devs")
    assert not unit.is_owned_by(repo_dir / "foo.txt", "management")
    assert unit.is_owned_by(repo_dir / "docs", "devs")
    assert unit.is_owned_by(repo_dir / "docs", "management")


def test_github_ownership_get_owners(fs: FakeFilesystem) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(
        fs,
        codeowners_content="""/src/ devs
/docs/ devs management""",
    )
    unit = GithubOwnerShip(repo_dir)
    assert unit.get_owners(repo_dir / "src") == ("devs",)
    assert unit.get_owners(repo_dir / "docs") == ("devs", "management")
    assert unit.get_owners(repo_dir / "scripts") == ()

    assert unit.get_first_owner(repo_dir / "docs") == "devs"
    assert unit.get_first_owner(repo_dir / "scripts") is None


def test_github_ownership_get_owners__second_overwrites_first__should_be_different_owners(
    fs: FakeFilesystem,
) -> None:
    repo_dir = _create_repo_path_with_codeowners_file(
        fs,
        codeowners_content="""/foo/bar bar-owner
/foo/bar/package package-owner""",
    )
    unit = GithubOwnerShip(repo_dir)
    assert unit.get_owners(repo_dir / "foo" / "bar") == ("bar-owner",)
    assert unit.get_owners(repo_dir / "foo" / "bar" / "package") == ("package-owner",)
    assert unit.get_owners(repo_dir / "foo" / "bar" / "something_else") == ("bar-owner",)


def test_get_ownership_entries_should_be_parsed_correctly(fs: FakeFilesystem) -> None:
    codeowners = Path("CODEOWNERS")
    fs.create_file(
        codeowners,
        contents="""/src/ devs
/docs/ devs management
# comment ignore""",
    )

    result = list(get_ownership_entries(codeowners))

    expect_entries_found = 2
    assert len(result) == expect_entries_found
    assert result[0].owners == ("devs",)
    assert result[1].owners == ("devs", "management")


def test_is_file_covered_by_pattern__exact_entries__returns_true() -> None:
    path = PurePath("a/b/c")
    prefix = PurePath("a/b/c")

    assert GithubOwnerShip.is_path_prefix(path, prefix)


@pytest.mark.parametrize("prefix", ["a/b", "a"])
def test_is_file_covered_by_pattern__proper_prefix__returns_true(prefix: str) -> None:
    path = PurePath("a/b/c")
    prefix_path = PurePath(prefix)

    assert GithubOwnerShip.is_path_prefix(path, prefix_path)


@pytest.mark.parametrize("prefix", ["aa", "a/bc"])
def test_is_file_covered_by_pattern__not_a_prefix__returns_false(prefix: str) -> None:
    path = PurePath("a/b/c")
    prefix_path = PurePath(prefix)

    assert not GithubOwnerShip.is_path_prefix(path, prefix_path)
