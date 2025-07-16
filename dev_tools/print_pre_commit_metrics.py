from __future__ import annotations

import json
import sys
from pathlib import Path

from pre_commit.constants import CONFIG_FILE

from dev_tools.check_useless_exclude_paths_hooks import Hook, load_hooks


def print_excluded_files_report(hooks_list: list[Hook]) -> None:
    hook_metrics_with_excluded_files: list[dict] = [
        {"hook_id": hook.id, "excluded_files_count": hook.count_excluded_files()}
        for hook in hooks_list
        if hook.count_excluded_files() > 0
    ]
    output_data = {
        "total_excluded_files": sum(
            hook_metric["excluded_files_count"] for hook_metric in hook_metrics_with_excluded_files
        ),
        "hooks": hook_metrics_with_excluded_files,
    }
    print(json.dumps(output_data, indent=2))


def main() -> int:
    repo_root = Path.cwd()
    pre_commit_config = repo_root / CONFIG_FILE
    hooks_list = load_hooks(repo_root, pre_commit_config)
    print_excluded_files_report(hooks_list)
    return 0


if __name__ == "__main__":
    sys.exit(main())
