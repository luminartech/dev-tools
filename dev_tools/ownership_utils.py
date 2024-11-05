# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

import re
import subprocess
import sys
from pathlib import Path, PurePath
from typing import Dict, Generator, Optional, Tuple


class FileNotFoundError(Exception):
    pass


class NotInDirectoryError(Exception):
    pass


class OwnerShipEntry:
    def __init__(self, pattern: str, owners: Tuple[str, ...], line_number: int) -> None:
        self.pattern: str = pattern
        self.owners: Tuple[str, ...] = owners
        self.line_number: int = line_number


# This is only defined in pathlib in Python 3.9.
def is_relative_to(subpath: PurePath, root: PurePath) -> bool:
    """Return True if subpath is relative to root or False."""
    try:
        subpath.relative_to(root)
    except ValueError:
        return False
    else:
        return True


def resolve_file_in_dir(dir: Path, file: Path) -> Path:
    """Return a path to `file` assuming it's in `dir` directory or its subdirs.

    `file` can be both relative to `dir` or absolute.
    `dir` can be both relative to current working dir or absolute.
    Raise an exception if `file` is not in `dir`.
    """
    print(f"dir: {dir}, file: {file}, file.is_absolute(): {file.is_absolute()}")
    if file.is_absolute():
        resolved_file = file.resolve()
        if not is_relative_to(resolved_file, dir.resolve()):
            message = f"file {resolved_file} is not in directory {dir.resolve()}"
            raise NotInDirectoryError(message)
    else:
        resolved_file = (dir / file).resolve()
    print(f"resolved_file: {resolved_file}")
    return resolved_file


class GithubOwnerShip:
    def __init__(self, repo_dir: Path, codeowners_file: Path = Path(".github") / "CODEOWNERS") -> None:
        self._ownerships = parse_ownership(resolve_file_in_dir(repo_dir, codeowners_file))
        self._repo_dir = repo_dir.resolve()
        self._cached_regex = CachedRegex()

    def is_owned_by(self, file: Path, codeowner: str) -> bool:
        return codeowner in self.get_owners(file)

    def get_first_owner(self, file: Path) -> Optional[str]:
        owners = self.get_owners(file)
        return owners[0] if owners else None

    def get_owners(self, file: Path) -> Tuple[str, ...]:
        for ownership in self._ownerships:
            if self.is_file_covered_by_pattern(file.relative_to(self._repo_dir), ownership.pattern):
                return ownership.owners

        return ()

    def is_file_covered_by_pattern(self, filepath_in_repo: Path, pattern: str) -> bool:
        """Implements the complete featureset demonstrated at https://docs.github.com/en/repositories/managing-your-
        repositorys-settings-and-features/customizing-your-repository/about-code-owners#example-of-a-codeowners-file."""
        filepath_string = str(filepath_in_repo)
        if "*" in pattern:
            return self._match_pattern_with_asterisks(filepath_string, filepath_in_repo.name, pattern)
        if pattern.startswith("/"):
            path_from_pattern = Path(pattern[1:].rstrip("/"))
            return path_from_pattern == filepath_in_repo or path_from_pattern in filepath_in_repo.parents
        return pattern.rstrip("/") in filepath_string

    def _match_pattern_with_asterisks(self, filepath_string: str, filename: str, pattern: str) -> bool:
        regex_pattern = pattern.replace("*", "(.*)")
        regex_pattern = regex_pattern[1:] if pattern.startswith("/") else f".*?{regex_pattern}"

        matches = self._cached_regex.match(regex_pattern, filepath_string)

        if pattern.endswith("/*"):
            return False if matches is None else bool(matches.groups()[-1] == filename)

        return matches is not None


class CachedRegex:
    """A wrapper around re.match to compile and cache regex patterns.

    It has unlimited size.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, re.Pattern[str]] = {}

    def match(self, needle: str, haystack: str, flags: int = 0) -> Optional[re.Match]:
        if needle not in self._cache:
            self._cache[needle] = re.compile(needle, flags)
        return self._cache[needle].match(haystack)


def parse_ownership(codeowners_file: Path) -> Tuple[OwnerShipEntry, ...]:
    """Return ownership in reverse order.

    Order is important. Last matching pattern in CODEOWNERS takes the most
    precedence.
    """
    return tuple(reversed(tuple(get_ownership_entries(codeowners_file))))


def get_ownership_entries(codeowners_file: Path) -> Generator[OwnerShipEntry, None, None]:
    with codeowners_file.open() as file:
        for line_number, line in enumerate(file.readlines(), start=1):
            current_line = line.strip()

            if current_line.startswith("#"):  # comment
                continue

            match = re.findall(r"(\S+)", current_line)
            if match:
                yield OwnerShipEntry(match[0], tuple(match[1:]), line_number)


def check_git(command: str, repo_dir: Path) -> str:
    return subprocess.check_output(f"git {command}".split(), cwd=repo_dir).decode(sys.stdout.encoding)
