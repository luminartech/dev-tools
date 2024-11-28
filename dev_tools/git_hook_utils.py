# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence


def parse_arguments(argv: Sequence[str] | None) -> Namespace:
    return create_default_parser().parse_args(argv)


def create_default_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*", type=Path)
    return parser
