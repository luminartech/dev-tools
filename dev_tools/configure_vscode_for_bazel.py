# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.
"""Generate VSCode configuration for selected Bazel C++ targets.

- generate launch.json debug configurations
- generate `compilation_commands.json`
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Sequence

MAX_TARGETS_WITHOUT_CONFIRMATION = 20


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
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
        "--generate-launch-json",
        action="store_true",
        help="Generate the `launch.json` file.",
    )
    parser.add_argument(
        "--no-generate-launch-json",
        dest="generate_launch_json",
        action="store_false",
        help="Do not generate the `launch.json` file.",
    )
    parser.set_defaults(generate_launch_json=True)
    parser.add_argument(
        "--generate-compile-commands",
        action="store_true",
        help="Generate the `compile_commands.json` file.",
    )
    parser.add_argument(
        "--no-generate-compile-commands",
        dest="generate_compile_commands",
        action="store_false",
        help="Do not generate the `compile_commands.json` file.",
    )
    parser.set_defaults(generate_compile_commands=True)
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Don't ask for confirmation.",
    )

    return parser.parse_args(argv)


def run_bazel_command(command: str, *args: str) -> str:
    cmd = ["bazel", command, "--ui_event_filters=-info", "--noshow_progress", *args]
    logging.debug("Running command: %s", " ".join(cmd))
    return subprocess.check_output(cmd).decode(sys.stdout.encoding)


def is_executable_rule(kind: str, entity: str) -> bool:
    return entity == "rule" and kind in ["cc_binary", "cc_test"]


def confirm_or_abort(message: str = "") -> bool:
    if input(f"{message} y/N: ").lower() != "y":
        logging.warning("Aborted.")
        return False
    return True


def confirm_if_too_many_labels(labels: set[str], force: bool) -> bool:  # noqa: FBT001
    if len(labels) > MAX_TARGETS_WITHOUT_CONFIRMATION and not force:
        logging.warning("Found %d bazel targets. Are you sure you want to add them all to launch.json?", len(labels))
        return confirm_or_abort()
    return True


def confirm_config_overwrite(config_location: Path, force: bool) -> bool:  # noqa: FBT001
    if config_location.exists() and not force:
        logging.warning("File %s already exists.", config_location.resolve())
        return confirm_or_abort("Do you want to overwrite it?")
    return True


def query_bazel_for_labels(pattern: str) -> str:
    return run_bazel_command("query", f"'{pattern}'", "--output=label_kind")


def get_label_from_bazel_query_line(line: str) -> str | None:
    vals = line.split()
    kind, entity, label = vals[0], vals[1], " ".join(vals[2:])
    return label if is_executable_rule(kind, entity) else None


def get_labels_from_bazel_query_output(output: str, pattern: str) -> set[str]:
    labels = {
        label for label in (get_label_from_bazel_query_line(line) for line in output.splitlines()) if label is not None
    }
    if not labels:
        logging.warning("No executable targets found for %s", pattern)
    return labels


def find_executable_labels(patterns: Sequence[str], force: bool) -> set[str]:  # noqa: FBT001
    logging.info("Searching for executable targets to generate launch.json...")
    labels_nested = (
        get_labels_from_bazel_query_output(query_bazel_for_labels(pattern), pattern) for pattern in patterns
    )
    labels = {label for labels in labels_nested for label in labels}

    logging.info("Found %d executable target(s).", len(labels))
    logging.debug("Executable labels: %s", labels)

    if confirm_if_too_many_labels(labels, force):
        return labels
    return set()  # we have no confirmation to continue


def remove_prefix_if_present(text: str, prefix: str) -> str:
    return text[len(prefix) :] if text.startswith(prefix) else text


def get_path_from_label(bazel_label: str) -> str:
    return remove_prefix_if_present(bazel_label, "//").replace(":", "/")


def get_new_launch_config(executable_labels: set[str]) -> dict[str, Any]:
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


def save_new_launch_config(new_config: dict[str, Any], config_location: Path, force: bool) -> bool:  # noqa: FBT001
    """Serializes the new_configuration to config_location.

    If the file already exists, asks for confirmation, unless force is set.
    """
    if confirm_config_overwrite(config_location, force):
        config_location.write_text(json.dumps(new_config, indent=4))
        logging.info("Saved new configuration to %s", config_location)
        return True
    return False


def update_launch_json(bazel_patterns: list[str], config_location: Path, force: bool) -> bool:  # noqa: FBT001
    if executable_labels := find_executable_labels(bazel_patterns, force):
        new_config = get_new_launch_config(executable_labels)
        return save_new_launch_config(new_config, config_location, force)
    return False


def update_cc_build_file(bazel_patterns: list[str], config_location: Path, force: bool) -> bool:  # noqa: FBT001
    if confirm_config_overwrite(config_location, force):
        sep = "," + "\n" + " " * 24
        config_location.write_text(
            textwrap.dedent(
                f"""
                load("@hedron_compile_commands//:refresh_compile_commands.bzl", "refresh_compile_commands")

                refresh_compile_commands(
                    name = "refresh_compile_commands",
                    targets = [
                        {sep.join(repr(p) for p in bazel_patterns)}
                    ],
                )
                """
            ).strip()
        )
        logging.info("Saved new BUILD.bazel to %s", config_location)
        return True
    return False


def get_workspace_root() -> Path:
    return Path(run_bazel_command("info", "workspace").strip())


def main() -> int:
    args = parse_arguments()
    lvl = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=lvl, format="%(asctime)s [%(levelname)s] %(message)s")

    if not shutil.which("bazel"):
        logging.warning("Bazel is required! Please install Bazel first.")
        return 1

    vscode_dir = get_workspace_root() / ".vscode"

    recommended_actions = []

    if args.generate_launch_json:
        if update_launch_json(args.bazel_pattern, vscode_dir / "launch.json", args.force):
            logging.info("You can now run the debug target(s) in VS Code.")
            recommended_actions.append(("bazel", "build", "--config=debug", *args.bazel_pattern))
        else:
            logging.error("No executable targets were found, no `launch.json` file was generated.")

    if args.generate_compile_commands and update_cc_build_file(
        args.bazel_pattern, vscode_dir / "BUILD.bazel", args.force
    ):
        logging.info("You can now generate the `compile_commands.json` file.")
        recommended_actions.append(("bazel", "build", *args.bazel_pattern))
        recommended_actions.append(("bazel", "run", "//.vscode:refresh_compile_commands"))

    logging.info("Remember to build the target(s) with:\n\n%s", "\n".join(" ".join(c) for c in recommended_actions))

    return 0


if __name__ == "__main__":
    sys.exit(main())
