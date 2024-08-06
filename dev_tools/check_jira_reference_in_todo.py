# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from dev_tools.git_hook_utils import parse_arguments


def line_has_incorrect_todo(line: str) -> bool:
    return (
        not re.compile(r"^.*(?=TODO\([A-Z]+\-[0-9]+\)\:).*").search(line)
        if re.compile(r"^.*(?=(?i:to-?do)|TO DO)(?!todo|toDouble|tOdometry)").search(line)
        else False
    )


def find_files_with_incorrect_jira_reference_in_todo(files: List[Path]) -> List[Dict[str, object]]:
    incorrect_files = []
    for file in files:
        lines = file.read_text(errors="ignore").splitlines()
        for line_number, line in enumerate(lines, 1):
            if line_has_incorrect_todo(line):
                incorrect_files.append({"file_path": file, "line_number": line_number, "line_content": line.strip()})

    return incorrect_files


def has_any_file_incorrect_jira_reference_in_todo(files: List[Path]) -> bool:

    if (incorrect_files := find_files_with_incorrect_jira_reference_in_todo(files)):
        print("\nThe following TODOs do not correspond to the JIRA-Ticket TODO format 'TODO(ABC-1234):':")
        for file in incorrect_files:
            print(f"{file['file_path']}:{file['line_number']}: error: '{file['line_content']}'")
        return True

    return False


def main(argv: Optional[Sequence[str]] = None) -> int:
    return 1 if has_any_file_incorrect_jira_reference_in_todo(parse_arguments(argv).filenames) else 0


if __name__ == "__main__":
    sys.exit(main())
