from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Sequence


def parse_arguments(argv: Optional[Sequence[str]]) -> Namespace:
    return create_default_parser().parse_args(argv)


def create_default_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*", type=Path)
    return parser
