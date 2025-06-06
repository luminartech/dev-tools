# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from dev_tools.configure_vscode_for_bazel import (
    find_executable_labels,
    get_label_from_bazel_query_line,
    get_new_launch_config,
    get_new_tasks_config,
    get_path_from_label,
    parse_arguments,
    save_new_json_config,
)

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


@patch(
    "dev_tools.configure_vscode_for_bazel.query_bazel_for_labels",
    MagicMock(return_value="cc_test rule //foo/bar:test1"),
)
def test__find_executable_labels__for_single_label__returns_it() -> None:
    assert find_executable_labels(["//foo/bar:..."], force=True) == {"//foo/bar:test1"}


@patch(
    "dev_tools.configure_vscode_for_bazel.query_bazel_for_labels",
    MagicMock(return_value="cc_test rule //foo/bar:test1\ncc_binary rule //foo/bar:main\n"),
)
def test__find_executable_labels__for_bigger_query__returns_combined_labels() -> None:
    assert find_executable_labels(["//foo/bar/..."], force=True) == {
        "//foo/bar:test1",
        "//foo/bar:main",
    }


@patch(
    "dev_tools.configure_vscode_for_bazel.query_bazel_for_labels",
    MagicMock(side_effect=["cc_test rule //foo/bar:test1", "cc_binary rule //foo/bar:main"]),
)
def test__find_executable_labels__for_two_queries__returns_combined_labels() -> None:
    assert find_executable_labels(["//foo/bar:test1", "//foo/bar:main"], force=True) == {
        "//foo/bar:test1",
        "//foo/bar:main",
    }


def test__get_label_from_bazel_query_line__for_label_with_space__returns_label_with_space() -> None:
    assert get_label_from_bazel_query_line("cc_test rule //foo/bar:test or not") == "//foo/bar:test or not"


def test__get_label_from_bazel_query_line__for_non_rule__returns_none() -> None:
    assert get_label_from_bazel_query_line("cc_test something //foo/bar:test1") is None


def test__get_path_from_label__for_label__returns_correct_fs_path() -> None:
    assert get_path_from_label("//foo/bar:test1") == "foo/bar/test1"


def test__get_new_launch_config__for_one_label__returns_correct_variables() -> None:
    config = get_new_launch_config({"//foo/bar:test1"})
    assert config["configurations"][0]["name"] == "(gdb) //foo/bar:test1"
    assert config["configurations"][0]["cwd"] == "${workspaceFolder}"
    assert config["configurations"][0]["variables"]["generated_by"] == "configure-vscode-for-bazel"
    assert config["configurations"][0]["program"].endswith(r"bazel-out/k8-dbg/bin/${binary_path}")


def test__get_new_tasks_config__for_one_label__returns_correct_command_line() -> None:
    config = get_new_tasks_config({"//foo/bar:test1"})
    assert config["tasks"][0]["command"] == "bazel"
    assert config["tasks"][0]["args"] == ["build", "//foo/bar:test1"]


def test__get_new_tasks_config__for_one_label_and_additional_args__returns_correct_command_line() -> None:
    config = get_new_tasks_config({"//foo/bar:test1"}, ["--config=dbg"])
    assert config["tasks"][0]["command"] == "bazel"
    assert config["tasks"][0]["args"] == ["build", "--config=dbg", "//foo/bar:test1"]


def test__save_new_json_config__when_it_doesnt_exist__creates_new_file(fs: FakeFilesystem) -> None:
    tmp_file = Path(fs.create_file("launch.json").path)
    save_new_json_config({"configurations": []}, config_location=tmp_file, force=True)
    assert "configurations" in tmp_file.read_text()


def test__save_new_json_config__when_it_exists__overwrites_it(fs: FakeFilesystem) -> None:
    tmp_file = Path(fs.create_file("launch.json").path)
    tmp_file.write_text('{"old_content": []}')
    save_new_json_config({"new_content": []}, config_location=tmp_file, force=True)
    assert "new_content" in tmp_file.read_text()
    assert "old_content" not in tmp_file.read_text()


def test__parse_arguments__for_two_patterns__returns_parsed_values() -> None:
    args = parse_arguments(["//foo/bar:test1", "//foo/bar:main"])
    assert args.bazel_pattern == ["//foo/bar:test1", "//foo/bar:main"]
    assert not args.force
    assert not args.verbose


def test__parse_arguments__for_no_patterns__raises_error() -> None:
    assert pytest.raises(SystemExit, parse_arguments, [])
