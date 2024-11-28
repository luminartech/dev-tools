# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Sequence

from dev_tools.git_hook_utils import parse_arguments

if TYPE_CHECKING:
    from pathlib import Path


def _sets_options_or_is_nolint(line: str) -> bool:
    return line.strip() in ["set -euxo pipefail", "# nolint(set_options)"]


def _is_valid_bash_file(filename: Path) -> bool:
    return any(_sets_options_or_is_nolint(line) for line in filename.open().readlines())


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv)

    invalid_bash_files = [filename for filename in args.filenames if not _is_valid_bash_file(filename)]
    for filename in invalid_bash_files:
        print(f"Error: {filename} does not contain 'set -euxo pipefail'")

    return 1 if invalid_bash_files else 0


if __name__ == "__main__":
    sys.exit(main())
