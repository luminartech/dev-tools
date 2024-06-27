# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from ruamel.yaml import YAML

from dev_tools.check_useless_exclude_paths_hooks import (
    Hook,
    has_excludes,
    have_non_existent_paths_or_duplicates,
    is_regex_pattern,
    load_hooks,
)


@pytest.mark.parametrize("pattern", [".*\\/conanfile.py", "\\.lock$", "^samples/ros1/src/"])
def test_is_regex_pattern_for_regex_should_be_true(pattern: str) -> None:
    assert is_regex_pattern(pattern)


def test_is_regex_pattern_for_no_regex_should_be_false() -> None:
    assert is_regex_pattern("packages/thirdparty/") is False


def test_from_hook_config_for_single_path(fs: FakeFilesystem) -> None:
    root_directory = Path("Test_directory/")
    fs.create_dir(root_directory)
    hook_instance = Hook.from_hook_config(root_directory, {"id": "buildifier", "exclude": "packages/thirdparty/"})

    assert has_excludes({"id": "check-snake-case", "exclude": "packages/thirdparty"})
    assert hook_instance.id == "buildifier"
    assert hook_instance.exclude_paths == [root_directory / Path("packages/thirdparty/")]


def test_from_hook_config_for_multiple_paths(fs: FakeFilesystem) -> None:
    root_directory = Path("Test_directory/")
    fs.create_dir(root_directory)
    hook_instance = Hook.from_hook_config(
        root_directory,
        {"id": "buildifier", "exclude": "(?x)^(\n  packages/thirdparty/|\n  python/aws_auth/\n)\n"},
    )

    assert hook_instance.id == "buildifier"
    assert hook_instance.exclude_paths == [
        root_directory / Path("packages/thirdparty/"),
        root_directory / Path("python/aws_auth/"),
    ]


def test_find_duplicates_for_duplicate_paths_should_return_duplicate_paths(fs: FakeFilesystem) -> None:
    fs.create_file(Path("Repo/existing_path1"))
    fs.create_file(Path("Repo/existing_path2"))
    hook_instance = Hook(
        "test_id",
        [Path("existing_path1"), Path("existing_path2"), Path("existing_path1"), Path("existing_path2")],
    )

    assert hook_instance.has_duplicates()
    assert hook_instance.find_duplicates() == [Path("existing_path1"), Path("existing_path2")]


def test_find_duplicates_for_no_duplicate_paths_should_return_empty_list(fs: FakeFilesystem) -> None:
    fs.create_file(Path("Repo/existing_path1"))
    fs.create_file(Path("Repo/existing_path2"))
    hook_instance = Hook("test_id", [Path("existing_path1"), Path("existing_path2")])

    assert not hook_instance.has_duplicates()
    assert hook_instance.find_duplicates() == []


def test_find_non_existing_paths_for_non_existing_files_should_return_non_existing_files(fs: FakeFilesystem) -> None:
    fs.create_file(Path("Repo/existing_path"))
    hook_instance = Hook(
        "test_id",
        [Path("Repo/existing_path"), Path("Repo/non_existing_path1"), Path("Repo/non_existing_path2")],
    )

    assert hook_instance.has_non_existing_paths()
    assert hook_instance.find_non_existing_paths() == [
        Path("Repo/non_existing_path1"),
        Path("Repo/non_existing_path2"),
    ]


def test_find_non_existing_paths_for_existing_files_should_return_empty_list(fs: FakeFilesystem) -> None:
    fs.create_file(Path("Repo/existing_path1"))
    fs.create_file(Path("Repo/existing_path2"))
    hook_instance = Hook("test_id", [Path("Repo/existing_path1"), Path("Repo/existing_path2")])

    assert not hook_instance.has_non_existing_paths()
    assert hook_instance.find_non_existing_paths() == []


def test_has_excludes_for_existing_excludes_should_return_true() -> None:
    assert has_excludes({"id": "check-snake-case", "exclude": "packages/thirdparty"})


def test_has_excludes_for_non_existing_excludes_should_return_false() -> None:
    assert not has_excludes({"id": "check-snake-case"})


def _create_yaml_content(yaml_file: Path, exclude: str) -> YAML:
    yaml = YAML()
    return yaml.dump(
        {
            "repos": [
                {
                    "repo": "meta",
                    "hooks": [
                        {"id": "check-hooks-apply"},
                    ],
                },
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": "check-snake-case",
                            "name": "check snake case",
                            "entry": "python3 foo.py",
                            "language": "python",
                            **({"exclude": exclude} if exclude else {}),
                        },
                    ],
                },
            ],
        },
        yaml_file,
    )


def test_load_hooks_for_no_exclude_file(fs: FakeFilesystem) -> None:
    root_directory = Path("Test_directory/")
    fs.create_dir(root_directory)
    config_file = root_directory / Path(".pre-commit-config.yaml")
    fs.create_file(config_file)
    _create_yaml_content(config_file, "")

    assert len(load_hooks(root_directory, config_file)) == 0


def test_load_hooks_for_exclude_files(fs: FakeFilesystem) -> None:
    root_directory = Path("Test_directory/")
    fs.create_dir(root_directory)
    config_file = root_directory / Path(".pre-commit-config.yaml")
    fs.create_file(config_file)
    _create_yaml_content(config_file, "(?x)^(python/aws_auth|packages/thirdparty/)")
    result = load_hooks(root_directory, config_file)

    assert len(result) == 1
    assert result[0].id == "check-snake-case"


def test_have_non_existent_paths_or_duplicates_for_non_existing_paths(
    capsys: pytest.CaptureFixture,
    fs: FakeFilesystem,
) -> None:
    fs.create_file(Path("Repo/existing_path"))
    assert have_non_existent_paths_or_duplicates(
        [
            Hook(
                "test_id",
                [Path("Repo/existing_path"), Path("Repo/non_existing_path1"), Path("Repo/non_existing_path2")],
            ),
        ],
    )
    output = capsys.readouterr().out
    assert "test_id" in output
    assert "non-existing" in output
    assert "non_existing_path1" in output
    assert "non_existing_path2" in output


def test_have_non_existent_paths_or_duplicates_for_duplicate_paths(
    capsys: pytest.CaptureFixture,
    fs: FakeFilesystem,
) -> None:
    fs.create_file(Path("Repo/existing_path1"))
    fs.create_file(Path("Repo/existing_path2"))
    assert have_non_existent_paths_or_duplicates(
        [
            Hook(
                "test_id",
                [
                    Path("Repo/existing_path1"),
                    Path("Repo/existing_path2"),
                    Path("Repo/existing_path1"),
                    Path("Repo/existing_path2"),
                ],
            ),
        ],
    )
    output = capsys.readouterr().out
    assert "test_id" in output
    assert "duplicates" in output
    assert "existing_path1" in output
    assert "existing_path2" in output
