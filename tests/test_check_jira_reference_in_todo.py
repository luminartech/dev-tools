# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dev_tools.check_jira_reference_in_todo import (
    find_files_with_incorrect_jira_reference_in_todo,
    has_any_file_incorrect_jira_reference_in_todo,
    line_has_incorrect_todo,
)


@pytest.mark.parametrize("content", ["TODO(ABC-1234):", "# TODO(ABC-1234):", "TODO(ABC-1234): remove code"])
def test_line_has_incorrect_todo_for_no_incorrect_todo(content: str) -> None:
    assert not line_has_incorrect_todo(content)


@pytest.mark.parametrize("content", ["toDouble()", "setOdometry()", "getOdometry"])
def test_line_has_incorrect_todo_for_no_undetected_todo(content: str) -> None:
    assert not line_has_incorrect_todo(content)


@pytest.mark.parametrize(
    "content",
    ["todo ", "TODO(ABC-1234)", "TODO ABC-1234:", "TODO (ABC-1234):", "ToDo ABC:", "Todo(ABC-1234):", "To-Do(ABC-1234):"],
)
def test_line_has_incorrect_todo_for_incorrect_todo(content: str) -> None:
    assert line_has_incorrect_todo(content)


@pytest.mark.parametrize("content", ["TODO(ABC-1234):", "# TODO(ABC-1234):", "TODO(ABC-1234): remove code"])
def test_find_files_with_correct_jira_reference_in_todo(fs: FakeFilesystem, content: str) -> None:
    fs.create_file(Path("Repo/file.py"), contents=content)

    assert find_files_with_incorrect_jira_reference_in_todo([Path("Repo/file.py")]) == []


@pytest.mark.parametrize(
    "content",
    ["TODO(ABC-1234)", "TODO ABC-1234:", "TODO (ABC-1234):", "ToDo ABC:", "Todo(ABC-1234):", "To-Do(ABC-1234):"],
)
def test_find_files_with_incorrect_jira_reference_in_todo(fs: FakeFilesystem, content: str) -> None:
    fs.create_file(Path("Repo/file.py"), contents=content)

    assert find_files_with_incorrect_jira_reference_in_todo([Path("Repo/file.py")]) == [
        {"file_path": Path("Repo/file.py"), "line_number": 1, "line_content": content},
    ]


@pytest.mark.parametrize("content", ["TODO(ABC-1234):", "# TODO(ABC-1234):", "TODO(ABC-1234): remove code"])
def test_has_any_file_incorrect_jira_reference_in_todo_for_no_incorrect_todo(
    fs: FakeFilesystem,
    content: str,
    capsys: pytest.CaptureFixture,
) -> None:
    fs.create_file(Path("Repo/file.py"), contents=content)

    assert not has_any_file_incorrect_jira_reference_in_todo([Path("Repo/file.py")])
    assert not capsys.readouterr().out


@pytest.mark.parametrize(
    "content",
    ["TODO(ABC-1234)", "TODO ABC-1234:", "TODO (ABC-1234):", "ToDo ABC:", "Todo(ABC-1234):", "To-Do(ABC-1234):"],
)
def test_has_any_file_incorrect_jira_reference_in_todo_for_incorrect_todo(
    fs: FakeFilesystem,
    content: str,
    capsys: pytest.CaptureFixture,
) -> None:
    fs.create_file(Path("Repo/file.py"), contents=content)

    assert has_any_file_incorrect_jira_reference_in_todo([Path("Repo/file.py")])
    output = capsys.readouterr().out
    assert "JIRA-Ticket" in output
    assert "TODO format" in output
    assert "TODO(ABC-1234):" in output
    assert content in output
