# Copyright (c) Luminar Technologies, Inc. All rights reserved.
# Licensed under the MIT License.

from pyfakefs.fake_filesystem import FakeFilesystem

from dev_tools.check_shellscript_set_options import main


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
