# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pyfakefs.helpers

from dev_tools.check_shellscript_set_options import main

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


EXECUTABLE_FILE = stat.S_IFREG | pyfakefs.helpers.PERM_EXE | pyfakefs.helpers.PERM_DEF_FILE


def test_pass_for_valid_file(fs: FakeFilesystem) -> None:
    file = "valid_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/bash
set -euxo pipefail
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 0


def test_pass_for_nolinted_file(fs: FakeFilesystem) -> None:
    file = "nolint_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/bash
# nolint(set_options)
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 0


def test_pass_for_sh_file(fs: FakeFilesystem) -> None:
    file = "sh_file.sh"
    fs.create_file(
        file,
        contents="""#!/bin/sh
set -eux
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 0


def test_pass_for_sh_file_from_env(fs: FakeFilesystem) -> None:
    file = "sh_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/env sh
set -eux
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 0


def test_pass_for_bash_file_from_suffix(fs: FakeFilesystem) -> None:
    file = "sh_file.bash"
    fs.create_file(
        file,
        contents="""
set -euxo pipefail
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 0


def test_pass_for_non_executable_file(fs: FakeFilesystem) -> None:
    file = "sh_file.sh"
    fs.create_file(
        file,
        contents="date",
    )

    assert main([str(file)]) == 0


def test_one_valid_and_one_invalid_file(fs: FakeFilesystem) -> None:
    valid_file = "sh_file.sh"
    fs.create_file(
        valid_file,
        contents="""#!/bin/sh
set -eux
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    invalid_file = "invalid.bash"
    fs.create_file(
        invalid_file,
        contents="""#!/bin/bash
set -eux
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(valid_file), str(invalid_file)]) == 1


def test_fail_for_file_without_shebang(fs: FakeFilesystem) -> None:
    file = "sh_file.sh"
    fs.create_file(
        file,
        contents="""
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 1


def test_fail_for_invalid_file(fs: FakeFilesystem) -> None:
    file = "invalid_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/bash
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 1


def test_fail_for_invalid_bash_file_from_suffix(fs: FakeFilesystem) -> None:
    file = "sh_file.bash"
    fs.create_file(
        file,
        contents="""
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 1


def test_fail_for_wrongly_formatted_nolinted_file(fs: FakeFilesystem) -> None:
    file = "nolint_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/bash
#nolint(set_options)
date
""",
        st_mode=EXECUTABLE_FILE,
    )

    assert main([str(file)]) == 1
