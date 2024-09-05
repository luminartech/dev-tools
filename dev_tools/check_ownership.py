# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

import sys
from argparse import Namespace
from enum import IntFlag, auto
from pathlib import Path
from typing import Dict, Generator, Iterable, Iterator, List, Optional, Set

from dev_tools.git_hook_utils import create_default_parser
from dev_tools.ownership_utils import GithubOwnerShip, OwnerShipEntry, check_git, get_ownership_entries


class ReturnCode(IntFlag):
    SUCCESS = 0
    ERROR_FOLDER_DOESNT_EXIST = auto()
    ERROR_DUPLICATE_LINES = auto()
    ERROR_MULTIPLE_FOLDER_OWNERS = auto()
    ERROR_RULE_IS_INEFFECTIVE = auto()
    ERROR_FILE_WITHOUT_TEAM_OWNERSHIP = auto()


def check_if_all_codeowners_folders_exist(repo_dir: Path, entries: Iterable[OwnerShipEntry]) -> ReturnCode:
    return_code = ReturnCode.SUCCESS
    for entry in entries:
        subfolder = entry.pattern
        subfolder = subfolder[1:] if subfolder.startswith("/") else str(Path("**") / subfolder)

        if "*" in subfolder:
            if is_empty(repo_dir.glob(subfolder)):
                print(
                    f"ERROR: No file/folder matches the ownership pattern '{subfolder}' in CODEOWNERS. "
                    "Remove the pattern if no longer needed."
                )
                return_code |= ReturnCode.ERROR_FOLDER_DOESNT_EXIST
        else:
            folder = repo_dir / subfolder
            if not folder.exists():
                print(
                    f"ERROR: No file/folder matches the ownership entry '{folder}' in CODEOWNERS. "
                    "Remove the entry if no longer needed."
                )
                return_code |= ReturnCode.ERROR_FOLDER_DOESNT_EXIST

    return return_code


class OwnerShipTreeNode:
    """Represents a node in filesystem tree."""

    def __init__(self) -> None:
        self.children: Dict[str, OwnerShipTreeNode] = {}
        self.owners: Set[str] = set()
        self.line_number: Optional[int] = None

    def add_or_return_child(self, child_name: str) -> "OwnerShipTreeNode":
        if child_name not in self.children:
            node = OwnerShipTreeNode()
            self.children[child_name] = node
            return node
        return self.children[child_name]


def check_if_codeowners_has_ineffective_rules(all_entries: List[OwnerShipEntry]) -> ReturnCode:
    def _populate_tree(entry: OwnerShipEntry, path_parts: Iterator[str], tree_node: OwnerShipTreeNode) -> ReturnCode:
        """Add an OwnerShipEntry to the tree representation of all ownership entries.

        Find exact duplicates, ie. rules which have exactly the same patterns, on
        the fly. Performs a depth-first search.
        """
        return_code = ReturnCode.SUCCESS
        try:
            name = path_parts.__next__()
            child_node = tree_node.add_or_return_child(name)
            return_code |= _populate_tree(entry, path_parts, child_node)
        except StopIteration:
            previous_owners = tree_node.owners
            if previous_owners:
                if previous_owners == set(entry.owners):
                    print(
                        f"ERROR: Ownership entry with pattern '{entry.pattern}' from line {tree_node.line_number} "
                        f"repeats in line {entry.line_number}. Remove the repetitions from CODEOWNERS."
                    )
                    return_code |= ReturnCode.ERROR_DUPLICATE_LINES
                else:
                    print(
                        f"ERROR: Ownership entry with pattern '{entry.pattern}' from line {tree_node.line_number} "
                        f"repeats in line {entry.line_number} with different owners. "
                        "Remove the repetitions from CODEOWNERS."
                    )
                    return_code |= ReturnCode.ERROR_MULTIPLE_FOLDER_OWNERS
            tree_node.owners = set(entry.owners)
            tree_node.line_number = entry.line_number
        return return_code

    def _find_ineffective_rules(
        tree_node: OwnerShipTreeNode, first_ancestor: Optional[OwnerShipTreeNode], current_path: Path
    ) -> ReturnCode:
        """Search the ownership tree for rules which are fully contained in another
        rule. They are ineffective (redundant).

        Performs a depth-first search.
        """
        if first_ancestor is not None and tree_node.owners == first_ancestor.owners:
            print(
                f"ERROR: Ownership entry with pattern '{current_path}' from line {tree_node.line_number} is redundant. "
                f"A more generic pattern is in line {first_ancestor.line_number}. "
                "Remove the redundant ones from CODEOWNERS."
            )
            return ReturnCode.ERROR_RULE_IS_INEFFECTIVE

        if len(tree_node.owners) > 0:
            first_ancestor = tree_node

        return_code = ReturnCode.SUCCESS
        for child_name, child_node in tree_node.children.items():
            return_code |= _find_ineffective_rules(child_node, first_ancestor, current_path / child_name)
        return return_code

    root_node = OwnerShipTreeNode()
    return_code = ReturnCode.SUCCESS
    for entry in all_entries:
        path = Path(entry.pattern)
        return_code |= _populate_tree(entry, path.parts.__iter__(), root_node)

    return_code |= _find_ineffective_rules(root_node, None, Path())
    return return_code


def get_codeowners_path(repo_dir: Path) -> Path:
    return repo_dir / ".github" / "CODEOWNERS"


def perform_all_codeowners_checks(repo_dir: Path) -> ReturnCode:
    codeowners = get_codeowners_path(repo_dir)
    return_code = ReturnCode.SUCCESS
    all_entries = list(get_ownership_entries(codeowners))

    return_code |= check_if_all_codeowners_folders_exist(repo_dir, all_entries)
    return_code |= check_if_codeowners_has_ineffective_rules(all_entries)

    if return_code != ReturnCode.SUCCESS:
        print(f"Errors found in file {codeowners}")

    return return_code


def is_empty(iterable: Generator[Path, None, None]) -> bool:
    return next(iterable, None) is None


def get_git_tracked_files(folder: Path) -> List[Path]:
    files = check_git(f"ls-files {folder.relative_to(folder)}", folder)
    return [folder / file for file in files.splitlines()]


def check_for_files_without_team_ownership(
    repo_dir: Path, changed_files: List[Path], codeowners_owner: Optional[str]
) -> ReturnCode:
    """The codeowners_owner should own ONLY the CODEOWNERS file."""
    if codeowners_owner is None:
        print("No codeowners-owner provided. Skipping check.")
        return ReturnCode.SUCCESS

    codeowners = get_codeowners_path(repo_dir)
    changed_files = [file.resolve() for file in changed_files]
    files_to_check = get_git_tracked_files(repo_dir) if codeowners in changed_files else changed_files
    ownership_service = GithubOwnerShip(repo_dir)
    files_owned_by_codeowners_file_owners = [
        file for file in files_to_check if file != codeowners and ownership_service.is_owned_by(file, codeowners_owner)
    ]
    print(f"files to check: {files_to_check}")
    print(f"codeowners: {codeowners}")
    print(f"changed_files: {changed_files}")
    if not files_owned_by_codeowners_file_owners:
        return ReturnCode.SUCCESS

    for file in files_owned_by_codeowners_file_owners:
        print(f"{file} should not be owned by {codeowners_owner}. Please find a different owner.")

    return ReturnCode.ERROR_FILE_WITHOUT_TEAM_OWNERSHIP


def parse_arguments() -> Namespace:
    parser = create_default_parser()
    parser.add_argument("--codeowners-owner", type=str, help="Team or person that should only own the CODEOWNERS file")
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    repo_root = Path.cwd()
    return perform_all_codeowners_checks(repo_root) | check_for_files_without_team_ownership(
        repo_root, args.filenames, args.codeowners_owner
    )


if __name__ == "__main__":
    sys.exit(main())
