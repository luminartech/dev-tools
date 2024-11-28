# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Sequence

from dev_tools.git_hook_utils import create_default_parser

if TYPE_CHECKING:
    import argparse


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = create_default_parser()
    parser.add_argument(
        "--max-lines",
        default=30,
        type=int,
        action="store",
        help="Maximum allowable number of lines",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv)

    are_all_files_ok = True
    for filename in args.filenames:
        file_content = filename.open().readlines()
        number_of_lines = len(file_content)
        if number_of_lines > args.max_lines:
            print(f"{filename} ({number_of_lines} lines) exceeds {args.max_lines} lines.")
            are_all_files_ok = False

    return 0 if are_all_files_ok else 1


if __name__ == "__main__":
    sys.exit(main())
