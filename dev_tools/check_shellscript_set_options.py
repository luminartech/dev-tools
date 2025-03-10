# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Sequence

from dev_tools.git_hook_utils import parse_arguments

if TYPE_CHECKING:
    from pathlib import Path


def _sets_options_or_is_nolint(line: str, expected_options: str) -> bool:
    return line.strip() in [expected_options, "# nolint(set_options)"]


def _is_valid_shell_file(filename: Path, expected_options: str) -> bool:
    lines = filename.read_text().splitlines()
    return any(_sets_options_or_is_nolint(line, expected_options) for line in lines)


def _does_shebang_match(program: str, first_line: str) -> bool:
    matches = re.match(rf"^#!.*{program}", first_line)
    return matches is not None


def _separate_bash_from_sh_files(filenames: Sequence[Path]) -> tuple[list[Path], list[Path]]:
    bash_files = []
    sh_files = []
    for filename in filenames:
        first_line = filename.open().readline()
        if _does_shebang_match("bash", first_line):
            bash_files.append(filename)
        elif _does_shebang_match("sh", first_line):
            sh_files.append(filename)
        else:
            msg = f"Unknown shell in {filename}: {first_line}. Only use this hook in combination with 'check-executables-have-shebangs' from https://github.com/pre-commit/pre-commit-hooks"
            raise ValueError(msg)

    return bash_files, sh_files


def _are_shell_files_valid(shell_files: list[Path], expected_options: str) -> bool:
    invalid_shell_files = [filename for filename in shell_files if not _is_valid_shell_file(filename, expected_options)]
    for filename in invalid_shell_files:
        print(f"Error: {filename} does not contain '{expected_options}'")

    return bool(not invalid_shell_files)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv)

    bash_files, sh_files = _separate_bash_from_sh_files(args.filenames)
    are_all_files_valid = _are_shell_files_valid(bash_files, "set -euxo pipefail")
    are_all_files_valid &= _are_shell_files_valid(sh_files, "set -eux")

    return 0 if are_all_files_valid else 1


if __name__ == "__main__":
    sys.exit(main())
