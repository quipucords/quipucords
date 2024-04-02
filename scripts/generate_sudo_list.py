"""Helper script to generate sudo list doc."""

import argparse
import filecmp
import sys
import tempfile
from pathlib import Path

import yaml


def collect_sudo_commands(path=None):
    """Collect all ansible cmds that require sudo."""
    if not path:
        path = Path("quipucords/scanner/network/runner")
    list_cmds = []
    for playbook in path.glob("roles/*/tasks/main.yml"):
        for task in yaml.safe_load(playbook.open()):
            if task.get("become", ""):
                list_cmds.append(task.get("raw", ""))
    list_cmds = [
        cmd.strip() for cmd in list_cmds if isinstance(cmd, str) and cmd.strip()
    ]
    list_cmds = sorted(set(list_cmds))

    return list_cmds


def generate_sudo_cmds_document():
    """Generate a document listing commands that require sudo."""
    list_cmds = collect_sudo_commands()
    document = ""
    document += "\n".join(cmd for cmd in list_cmds if cmd.strip())
    return document


def create_document_file(file_path):
    """Create a txt file containing a list of commands that require sudo."""
    document = generate_sudo_cmds_document()
    file = Path(file_path)
    file.write_text(document)


def compare_sudo_cmds_lists(file_path):
    """Compare the most updated sudo list with an existing one."""
    generated_doc = generate_sudo_cmds_document()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(generated_doc.encode())
        try:
            if not filecmp.cmp(temp_file.name, file_path):
                sys.stderr.write(
                    "Error: The sudo command list document has been modified.\n"
                )
        except FileNotFoundError:
            sys.stderr.write(f"Error: {file_path} has not been found.\n")
        finally:
            Path(temp_file.name).unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["docs", "compare"], help="Command to execute"
    )
    parser.add_argument("file_path", help="Path to the file")

    args = parser.parse_args()

    if args.command == "docs":
        create_document_file(args.file_path)
    elif args.command == "compare":
        compare_sudo_cmds_lists(args.file_path)
