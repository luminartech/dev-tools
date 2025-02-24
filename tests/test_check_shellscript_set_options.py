# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from dev_tools.check_shellscript_set_options import main

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


def test_pass_for_valid_file(fs: FakeFilesystem) -> None:
    file = "valid_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/bash
set -euxo pipefail
date
""",
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
    )

    assert main([str(file)]) == 0


def test_pass_for_sh_file(fs: FakeFilesystem) -> None:
    file = "sh_file.sh"
    fs.create_file(
        file,
        contents="""#!/bin/sh
# set -eux
date
""",
    )

    assert main([str(file)]) == 1


def test_one_valid_and_one_invalid_file(fs: FakeFilesystem) -> None:
    valid_file = "sh_file.sh"
    fs.create_file(
        valid_file,
        contents="""#!/bin/sh
# set -eux
date
""",
    )

    invalid_file = "invalid.bash"
    fs.create_file(
        invalid_file,
        contents="""#!/bin/bash
# set -eux
date
""",
    )

    assert main([str(valid_file), str(invalid_file)]) == 1


def test_throw_for_file_without_shebang(fs: FakeFilesystem) -> None:
    file = "sh_file.sh"
    fs.create_file(
        file,
        contents="""
date
""",
    )

    with pytest.raises(ValueError, match="Unknown shell"):
        main([str(file)])


def test_fail_for_invalid_file(fs: FakeFilesystem) -> None:
    file = "invalid_file.sh"
    fs.create_file(
        file,
        contents="""#!/usr/bin/bash
date
""",
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
    )

    assert main([str(file)]) == 1
