"""Tests for utils.misc.is_valid_cache_file."""

from pathlib import Path

from utils.misc import is_valid_cache_file


def test_file_exists_none_false():
    """None path is not a file."""
    assert not is_valid_cache_file(None)


def test_file_exists_not_a_file_false(tmpdir):
    """Directory path is not a file."""
    assert not is_valid_cache_file(tmpdir)


def test_file_exists_bogus_path_false(faker):
    """Bogus path is not a file."""
    assert not is_valid_cache_file(str(faker.slug()))


def test_file_exists_empty_file_false(tmpdir, faker):
    """Empty file is not a valid cache file."""
    empty_path = Path(tmpdir) / faker.slug()
    empty_path.touch()
    assert not is_valid_cache_file(str(empty_path))


def test_file_exists_unreadable_file_false(tmpdir, faker):
    """Empty file is not a valid cache file."""
    unreadable_path = Path(tmpdir) / faker.slug()
    unreadable_path.write_text(faker.slug())
    unreadable_path.chmod(0o000)
    assert not is_valid_cache_file(str(unreadable_path))


def test_file_exists_normal_file_true(tmpdir, faker):
    """Normal nonzero-length readable file is a valid cache file."""
    file_path = Path(tmpdir) / faker.slug()
    file_path.touch()
    file_path.write_text(faker.slug())
    assert is_valid_cache_file(str(file_path))
