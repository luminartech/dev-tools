from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dev_tools.find_owner import get_owners, get_subitems


def test_find_owner_for_non_existent_item_raises() -> None:
    with pytest.raises(FileNotFoundError):
        get_owners(Path("non_existent_file"), 0)


def test_get_subitems(fs: FakeFilesystem) -> None:
    # Level 0
    parent_dir = Path("parent").resolve()
    fs.create_dir(parent_dir)
    # Level 1
    readme = parent_dir / "readme.md"
    fs.create_file(readme)
    src_dir = parent_dir / "src"
    fs.create_dir(src_dir)
    include_dir = parent_dir / "include"
    fs.create_dir(include_dir)
    # Level 2
    cpp_file = src_dir / "main.cpp"
    fs.create_file(cpp_file)
    header_file = include_dir / "header.h"
    fs.create_file(header_file)
    test_dir = src_dir / "tests"
    fs.create_dir(test_dir)

    assert get_subitems(parent_dir, 0) == [parent_dir]
    assert get_subitems(parent_dir, 1) == [include_dir, readme, src_dir]
    assert get_subitems(parent_dir, 2) == [header_file, cpp_file, test_dir]
