# Dev Tools

This is a collection of Luminar's development tools.
These tools are used to help developers in their day-to-day tasks.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Hooks](#hooks)
  - [`check-build-file-without-extensions`](#check-build-file-without-extensions)
  - [`check-snake-case`](#check-snake-case)
  - [`check-cpp-and-cu-unit-test-naming-pattern`](#check-cpp-and-cu-unit-test-naming-pattern)
  - [`check-no-dashes`](#check-no-dashes)
  - [`check-number-of-lines-count`](#check-number-of-lines-count)
  - [`check-shellscript-set-options`](#check-shellscript-set-options)
  - [`check-jira-reference-in-todo`](#check-jira-reference-in-todo)
  - [`check-non-existing-and-duplicate-excludes`](#check-non-existing-and-duplicate-excludes)

<!-- mdformat-toc end -->

## Hooks

### `check-build-file-without-extensions`

Check that `BUILD` files have a `.bazel` ending.
`BUILD.bazel` file is the recommended way to name these files.

### `check-snake-case`

Check that all source code files are `snake_case`.
We don't want to use `camelCase` or `kebab-case` file names.

### `check-cpp-and-cu-unit-test-naming-pattern`

Check that all C++ and Cuda unit test files end with `_test.cpp` or `_test.cu`.

### `check-no-dashes`

Check that no file dashes in their name.

### `check-number-of-lines-count`

Check that number of lines in do not exceed max-lines.
Use `--max-lines=<number>` to set the maximum number of lines.
Default is 30 for shell scripts.

### `check-shellscript-set-options`

Check if options are set with `set -euxo pipefail`.
Use `# nolint(set_options)` to ignore this check.

### `check-jira-reference-in-todo`

Check that all TODO comments follow the same pattern and link a Jira ticket: `TODO(ABC-1234): ...`.

### `check-non-existing-and-duplicate-excludes`

Check for non existing and duplicate paths in `.pre-commit-config.yaml`.
Background: In a big codebase, the exclude lists can be quite long and it's easy to make a typo or forget to remove an entry when it's no longer needed.
