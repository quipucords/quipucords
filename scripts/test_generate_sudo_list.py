"""Tests for generate sudo list script."""

from pathlib import Path
from unittest import mock

import pytest

from scripts.generate_sudo_list import (
    collect_sudo_commands,
    compare_sudo_cmds_lists,
    create_document_file,
    generate_sudo_cmds_document,
)


@pytest.fixture
def playbook_content_with_sudo():
    """Return playbook content with sudo cmds."""
    playbook_content = """
- name: Task 1
  raw: sudo command1
  become: yes

- name: Task 2
  raw: sudo command2
  become: yes

- name: Task 3
  raw: command3
"""
    return playbook_content


@pytest.fixture
def playbook_content_without_sudo():
    """Return playbook content with no cmds requiring sudo."""
    playbook_content = """
- name: Task 1
  raw: command1
  become: no

- name: Task 2
  raw: command2
"""
    return playbook_content


@pytest.fixture
def playbook_content_mixed_cmds():
    """Return playbook content with a mix of sudo and non-sudo cmds."""
    playbook_content = """
- name: Task 1
  raw: sudo command1
  become: yes

- name: Task 2
  raw: command2
"""
    return playbook_content


@pytest.fixture
def return_playbook_path(
    tmp_path,
    playbook_content_with_sudo,
    playbook_content_without_sudo,
    playbook_content_mixed_cmds,
    request,
):
    """Return the path to a temporary playbook file."""
    test_name = request.node.name
    if test_name.endswith("with_sudo"):
        playbook = playbook_content_with_sudo
    elif test_name.endswith("without_sudo"):
        playbook = playbook_content_without_sudo
    elif test_name.endswith("mixed_cmds"):
        playbook = playbook_content_mixed_cmds

    path = tmp_path / "quipucords" / "scanner" / "network" / "runner"
    path.mkdir(parents=True, exist_ok=True)

    role_dir = path / "roles" / "roles1" / "tasks"
    role_dir.mkdir(parents=True, exist_ok=True)

    main_yml_path = Path(role_dir / "main.yml")
    main_yml_path.write_text(playbook)
    yield path


@pytest.fixture
def generated_document_mock():
    """Return sudo cmds document."""
    with mock.patch(
        "scripts.generate_sudo_list.generate_sudo_cmds_document",
        return_value="sudo command 1\nsudo command 2\n",
    ) as mock_obj:
        yield mock_obj


def test_collect_commands_with_sudo(return_playbook_path):
    """Verify if all the sudo raw commands are collected correctly."""
    expected_cmds = [
        "sudo command1",
        "sudo command2",
    ]
    cmds = collect_sudo_commands(return_playbook_path)
    assert cmds == expected_cmds


def test_collect_commands_without_sudo(return_playbook_path):
    """Verify that non-sudo raw commands are not collected."""
    cmds = collect_sudo_commands(return_playbook_path)
    assert cmds == []


def test_collect_mixed_cmds(return_playbook_path):
    """Verify that only sudo cmds are being collected."""
    cmds = collect_sudo_commands(return_playbook_path)
    assert cmds == ["sudo command1"]


@mock.patch(
    "scripts.generate_sudo_list.collect_sudo_commands",
    return_value=["sudo command 1", "sudo command 2"],
)
def test_document_generation(list_cmds):
    """Verify if sudo cmd document is being generated correctly."""
    document = generate_sudo_cmds_document()
    assert document == "sudo command 1\nsudo command 2\n"


def test_file_creation(tmp_path, generated_document_mock):
    """Verify if sudo file is being created with correct cmds."""
    file_path = tmp_path / "sudo_list.txt"
    create_document_file(file_path)
    assert file_path.exists()
    expected = ["sudo command 1\n", "sudo command 2\n"]

    with file_path.open("r") as f:
        lines = f.readlines()
    assert lines == expected
    file_path.unlink()


def test_compare_lists_equal_files(tmp_path, capsys):
    """Verify expected output for equal sudo command lists."""
    file_path = tmp_path / "sudo_list.txt"
    with mock.patch("scripts.generate_sudo_list.filecmp.cmp", return_value=True):
        compare_sudo_cmds_lists(file_path)
    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""


def test_compare_lists_diff_files(tmp_path, capsys):
    """Verify expected output for different sudo command lists."""
    file_path = tmp_path / "sudo_list.txt"
    with (
        mock.patch("scripts.generate_sudo_list.filecmp.cmp", return_value=False),
        pytest.raises(SystemExit),
    ):
        compare_sudo_cmds_lists(file_path)
    expected_stderr = "Error: The sudo command list document has been modified.\n"
    out, err = capsys.readouterr()

    assert err == expected_stderr
    assert out == ""


def test_compare_lists_nonexistent_file(tmp_path, capsys):
    """Verify expected output for nonexistent sudo command file path."""
    file_path = tmp_path / "sudo_list.txt"
    with (
        mock.patch(
            "scripts.generate_sudo_list.filecmp.cmp", side_effect=FileNotFoundError()
        ),
        pytest.raises(SystemExit),
    ):
        compare_sudo_cmds_lists(file_path)
    expected_stderr = f"Error: {file_path} has not been found.\n"
    out, err = capsys.readouterr()

    assert err == expected_stderr
    assert out == ""
