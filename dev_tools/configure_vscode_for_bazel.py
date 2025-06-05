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


def add_run_and_debug_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--generate-launch-json",
        action="store_true",
        help="Generate the `launch.json` file containing gdb targets. This is the default.",
    )
    parser.add_argument(
        "--no-generate-launch-json",
        dest="generate_launch_json",
        action="store_false",
        help="Do not generate the `launch.json` file.",
    )
    # TODO(#80): use https://docs.python.org/3/library/argparse.html#argparse.BooleanOptionalAction with Python >= 3.9 # noqa: FIX002
    parser.set_defaults(generate_launch_json=True)

    parser.add_argument(
        "--generate-build-targets",
        action="store_true",
        help="Generate the `tasks.json` file containing build targets. If --generate-launch-json is set, the gdb targets will depend on the build targets. This is the default.",
    )
    parser.add_argument(
        "--no-generate-build-targets",
        dest="generate_build_targets",
        action="store_false",
        help="Do not generate the build targets in the `tasks.json` file.",
    )
    # TODO(#80): use https://docs.python.org/3/library/argparse.html#argparse.BooleanOptionalAction with Python >= 3.9 # noqa: FIX002
    parser.set_defaults(generate_build_targets=True)

    parser.add_argument(
        "--generate-compile-commands",
        action="store_true",
        help="Generate the `compile_commands.json` file. This is the default.",
    )
    parser.add_argument(
        "--no-generate-compile-commands",
        dest="generate_compile_commands",
        action="store_false",
        help="Do not generate the `compile_commands.json` file.",
    )
    # TODO(#80): use https://docs.python.org/3/library/argparse.html#argparse.BooleanOptionalAction with Python >= 3.9 # noqa: FIX002
    parser.set_defaults(generate_compile_commands=True)


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
        "--build",
        action="store_true",
        help="Run recommended bazel build/run actions.",
    )

    parser.add_argument(
        "--additional-debug-arg",
        type=str,
        nargs="*",
        default=[],
        action="extend",
        help="Additional arguments to pass to the bazel build command when building targets for the `launch.json` and `tasks.json`.",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Don't ask for confirmation.",
    )
    parser.add_argument(
        "--additional-compile-commands-arg",
        type=str,
        nargs="*",
        default=[],
        action="extend",
        help="Additional arguments to pass to the `compile_commands.json` refresh template.",
    )

    add_run_and_debug_arguments(parser)

    return parser.parse_args(argv)


def build_bazel_command(command: str, *args: str, verbose: bool = False) -> list[str]:
    quiet_args = [] if verbose else ["--ui_event_filters=-info", "--noshow_progress"]
    return ["bazel", command, *quiet_args, *args]


def run_bazel_command(command: str, *args: str, verbose: bool = False) -> None:
    """Run a Bazel command and check for exit code.

    Output is forwarded to the console.
    """
    cmd = build_bazel_command(command, *args, verbose=verbose)
    logging.debug("Running command: %s", " ".join(cmd))
    subprocess.check_call(cmd)


def run_bazel_command_output(command: str, *args: str) -> str:
    """Run a Bazel command and return its output as a string."""
    cmd = build_bazel_command(command, *args)
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
    return run_bazel_command_output("query", f"'{pattern}'", "--output=label_kind")


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


def get_new_tasks_config(executable_labels: set[str], additional_debug_args: list[str]) -> dict[str, Any]:
    return {
        "version": "2.0.0",
        "tasks": [
            {
                "label": f"(bazel build): {label}",
                "type": "process",
                "command": "bazel",
                "group": {
                    "kind": "build",
                },
                "args": [
                    "build",
                    *additional_debug_args,
                    label,
                ],
                "presentation": {
                    "clear": True,
                },
                "detail": f"bazel build {' '.join(additional_debug_args)}",
            }
            for label in executable_labels
        ],
    }


def save_new_json_config(new_config: dict[str, Any], config_location: Path, force: bool) -> bool:  # noqa: FBT001
    """Serializes the new_configuration to config_location.

    If the file already exists, asks for confirmation, unless force is set.
    """
    if confirm_config_overwrite(config_location, force):
        config_location.write_text(json.dumps(new_config, indent=4))
        logging.info("Saved new configuration to %s", config_location)
        return True
    return False


def update_launch_json(executable_labels: set[str], config_location: Path, force: bool) -> bool:  # noqa: FBT001
    if not executable_labels:
        return False
    new_config = get_new_launch_config(executable_labels)
    return save_new_json_config(new_config, config_location, force)


def update_tasks_json(
    executable_labels: set[str], config_location: Path, additional_debug_args: list[str], *, force: bool = False
) -> bool:
    if not executable_labels:
        return False
    new_config = get_new_tasks_config(executable_labels, additional_debug_args)
    return save_new_json_config(new_config, config_location, force)


def update_cc_build_file(bazel_patterns: list[str], bazel_args: list[str], config_location: Path, force: bool) -> bool:  # noqa: FBT001
    if confirm_config_overwrite(config_location, force):
        args = " ".join(bazel_args)
        targets = dict.fromkeys(bazel_patterns, args)
        config_location.write_text(
            textwrap.dedent(
                f"""
                load("@hedron_compile_commands//:refresh_compile_commands.bzl", "refresh_compile_commands")

                refresh_compile_commands(
                    name = "refresh_compile_commands",
                    targets = {targets},
                )
                """
            ).strip()
        )
        logging.info("Saved new BUILD.bazel to %s", config_location)
        return True
    return False


def get_workspace_root() -> Path:
    return Path(run_bazel_command_output("info", "workspace").strip())


def configure_logging(*, verbose: bool) -> None:
    lvl = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=lvl, format="%(asctime)s [%(levelname)s] %(message)s")


def check_dependencies() -> bool:
    if not shutil.which("bazel"):
        logging.warning("Bazel is required! Please install Bazel first.")
        return False
    return True


def setup_vscode_directory(vscode_dir: Path) -> None:
    if not vscode_dir.exists():
        logging.info("Creating .vscode directory in the workspace root.")
        vscode_dir.mkdir(parents=True)


def generate_executable_labels(args: argparse.Namespace) -> set[str]:
    if args.generate_launch_json or args.generate_build_targets:
        return find_executable_labels(args.bazel_pattern, args.force)
    return set()


def handle_tasks_json_generation(args: argparse.Namespace, executable_labels: set[str], vscode_dir: Path) -> None:
    if args.generate_build_targets:
        if update_tasks_json(executable_labels, vscode_dir / "tasks.json", args.additional_debug_arg, force=args.force):
            logging.info(
                "Build targets generated in `tasks.json`. Consider using Task: Run Build Task from the Command Palette."
            )
        else:
            logging.error("No executable targets found, no `tasks.json` generated.")


def handle_launch_json_generation(
    args: argparse.Namespace, executable_labels: set[str], vscode_dir: Path, recommended_actions: list[tuple[str, ...]]
) -> None:
    if args.generate_launch_json:
        success = update_launch_json(executable_labels, vscode_dir / "launch.json", args.force)
        if success:
            logging.info("You can now run the debug target(s) in VS Code.")
            if not args.generate_build_targets:
                recommended_actions.append(("bazel", "build", *args.additional_debug_arg, *args.bazel_pattern))
        else:
            logging.error("No executable targets found, no `launch.json` generated.")


def handle_compile_commands_generation(
    args: argparse.Namespace, vscode_dir: Path, recommended_actions: list[tuple[str, ...]]
) -> None:
    if args.generate_compile_commands:
        success = update_cc_build_file(
            args.bazel_pattern, args.additional_compile_commands_arg, vscode_dir / "BUILD.bazel", args.force
        )
        if success:
            logging.info("You can now generate the `compile_commands.json` file.")
            recommended_actions.extend(
                [
                    ("bazel", "build", *args.additional_compile_commands_arg, *args.bazel_pattern),
                    ("bazel", "run", "//.vscode:refresh_compile_commands"),
                ]
            )


def execute_recommended_actions(args: argparse.Namespace, recommended_actions: list[tuple[str, ...]]) -> None:
    if recommended_actions:
        if args.build:
            for action in recommended_actions:
                # action format is ("bazel", "command", "arg1", "arg2", ...)
                run_bazel_command(*action[1:], verbose=args.verbose)
        else:
            # If not building immediately, provide suggestions to the user
            suggested_cmds = "\n".join(" ".join(cmd) for cmd in recommended_actions)
            logging.info("Remember to re-build the target(s) with:\n\n%s", suggested_cmds)


def main() -> int:
    args = parse_arguments()
    configure_logging(verbose=args.verbose)

    if not check_dependencies():
        return 1

    vscode_dir = get_workspace_root() / ".vscode"
    setup_vscode_directory(vscode_dir)

    executable_labels = generate_executable_labels(args)

    recommended_actions: list[tuple[str, ...]] = []
    handle_tasks_json_generation(args, executable_labels, vscode_dir)
    handle_launch_json_generation(args, executable_labels, vscode_dir, recommended_actions)
    handle_compile_commands_generation(args, vscode_dir, recommended_actions)

    execute_recommended_actions(args, recommended_actions)

    return 0


if __name__ == "__main__":
    sys.exit(main())
