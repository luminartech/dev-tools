# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.
"""Generate a VSCode's launch.json debug configurations for selected Bazel C++
targets."""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

MAX_TARGETS_WITHOUT_CONFIRMATION = 20


def parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bazel_pattern",
        type=str,
        nargs="+",
        help="A Bazel pattern to scan for runnable targets. Example: //foo/bar/...",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Don't ask for confirmation.",
    )

    return parser.parse_args(argv)


def is_executable_rule(kind: str, entity: str) -> bool:
    return entity == "rule" and kind in ["cc_binary", "cc_test"]


def confirm_or_abort(message: str = "") -> None:
    if input(f"{message} y/N: ").lower() != "y":
        logging.warning("Aborted.")
        sys.exit(1)


def confirm_if_too_many_labels(labels: Set[str], force: bool) -> None:  # noqa: FBT001
    if len(labels) > MAX_TARGETS_WITHOUT_CONFIRMATION and not force:
        logging.warning("Found %d bazel targets. Are you sure you want to add them all to launch.json?", len(labels))
        confirm_or_abort()


def query_bazel_for_labels(pattern: str) -> str:
    cmd = ["bazel", "query", f"'{pattern}'", "--output=label_kind"]
    logging.info("Running command: %s", " ".join(cmd))
    return subprocess.check_output(cmd).decode(sys.stdout.encoding)


def get_label_from_bazel_query_line(line: str) -> Optional[str]:
    vals = line.split()
    kind, entity, label = vals[0], vals[1], " ".join(vals[2:])
    return label if is_executable_rule(kind, entity) else None


def get_labels_from_bazel_query_output(output: str, pattern: str) -> Set[str]:
    labels = {
        label for label in (get_label_from_bazel_query_line(line) for line in output.splitlines()) if label is not None
    }
    if not labels:
        logging.warning("No executable targets found for %s", pattern)
    return labels


def quit_if_no_labels_found(all_labels: set) -> None:
    if not all_labels:
        logging.error("In total, no executable targets were found. Aborting.")
        sys.exit(1)


def find_executable_labels(patterns: Sequence[str], force: bool) -> Set[str]:  # noqa: FBT001
    logging.info("Searching for executable targets to generate launch.json...")
    labels_nested = (
        get_labels_from_bazel_query_output(query_bazel_for_labels(pattern), pattern) for pattern in patterns
    )
    labels = {label for labels in labels_nested for label in labels}

    logging.info("Found %d executable target(s).", len(labels))
    logging.debug("Executable labels: %s", labels)

    quit_if_no_labels_found(labels)
    confirm_if_too_many_labels(labels, force)
    return labels


def remove_prefix_if_present(text: str, prefix: str) -> str:
    return text[len(prefix) :] if text.startswith(prefix) else text


def get_path_from_label(bazel_label: str) -> str:
    return remove_prefix_if_present(bazel_label, "//").replace(":", "/")


def get_new_config(executable_labels: Set[str]) -> Dict[str, Any]:
    return {
        "version": "0.2.0",
        "configurations": [
            {
                "name": f"(gdb) {label}",
                "type": "cppdbg",
                "request": "launch",
                "program": r"${workspaceFolder}/bazel-out/k8-dbg/bin/${binary_path}",
                "args": [],
                "stopAtEntry": False,
                "cwd": r"${workspaceFolder}",
                "environment": [],
                "externalConsole": False,
                "MIMode": "gdb",
                "setupCommands": [
                    {
                        "description": "Enable pretty-printing for gdb",
                        "text": "-enable-pretty-printing",
                        "ignoreFailures": True,
                    }
                ],
                "miDebuggerPath": "/usr/bin/gdb",
                "variables": {
                    "binary_path": get_path_from_label(label),
                    "generated_by": "configure-vscode-for-bazel",
                },
            }
            for label in executable_labels
        ],
    }


def save_new_config(new_config: Dict[str, Any], config_location: Path, force: bool) -> None:  # noqa: FBT001
    """Serializes the new_configuration to config_location.

    If the file already exists, asks for confirmation, unless force is set.
    """
    if config_location.exists() and not force:
        logging.warning("File %s already exists.", config_location.resolve())
        confirm_or_abort("Do you want to overwrite it?")
    config_location.write_text(json.dumps(new_config, indent=4))
    logging.info("Saved new configuration to %s", config_location)


def print_build_reminder(bazel_patterns: List[str]) -> None:
    infix = "eg. " if len(bazel_patterns) > 1 else ""
    logging.info(
        "Remember to build the target(s) beforehand with %s `bazel build --config=debug %s`.", infix, bazel_patterns[0]
    )


def update_launch_json(bazel_patterns: List[str], config_location: Path, force: bool) -> None:  # noqa: FBT001
    executable_labels = find_executable_labels(bazel_patterns, force)
    new_config = get_new_config(executable_labels)
    save_new_config(new_config, config_location, force)


def get_workspace_root() -> Path:
    cmd = ["bazel", "info", "workspace"]
    logging.info("Running command: %s", " ".join(cmd))
    return Path(subprocess.check_output(cmd).decode(sys.stdout.encoding).strip())


def main() -> int:
    args = parse_arguments()
    lvl = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=lvl, format="%(asctime)s [%(levelname)s] %(message)s")

    if not shutil.which("bazel"):
        logging.warning("Bazel is required! Please install Bazel first.")
        return 1

    update_launch_json(args.bazel_pattern, get_workspace_root() / ".vscode" / "launch.json", args.force)

    logging.info("You can now run the debug target(s) in VS Code.")
    print_build_reminder(args.bazel_pattern)
    return 0


if __name__ == "__main__":
    sys.exit(main())
