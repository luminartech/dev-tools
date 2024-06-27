from pyfakefs.fake_filesystem import FakeFilesystem

from dev_tools.check_number_of_lines_count import main

LONG_FILE_CONTENTS = "foo\n" * 60
SHORT_FILE_CONTENTS = "bar\n" * 2


def test_return_0_on_short_enough_file(fs: FakeFilesystem) -> None:
    file = "foo.py"
    fs.create_file(file, contents=SHORT_FILE_CONTENTS)
    assert main([file]) == 0


def test_return_1_as_soon_as_one_file_is_too_long(fs: FakeFilesystem) -> None:
    file_a = "foo.py"
    file_b = "bar.py"
    fs.create_file(file_a, contents=SHORT_FILE_CONTENTS)
    fs.create_file(file_b, contents=LONG_FILE_CONTENTS)
    assert main([file_a, file_b]) == 1
