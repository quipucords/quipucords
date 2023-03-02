"""Utilities for testing processors."""


def ansible_result(stdout, rc=0):  # pylint: disable=invalid-name
    """Make an Ansible result dictionary for a successful result."""
    return {"rc": rc, "stdout": stdout, "stdout_lines": stdout.splitlines()}


def ansible_results(results):
    """Make an Ansible result dictionary for a with_items task."""
    return {
        "results": [
            {
                "item": result.get("item", ""),
                "stdout": result["stdout"],
                "stdout_lines": result["stdout"].splitlines(),
                "rc": result.get("rc", 0),
            }
            for result in results
        ]
    }


def ansible_item(name, stdout, rc=0):  # pylint: disable=invalid-name
    """Make an item for an Ansible with-items dictionary."""
    return {
        "item": name,
        "rc": rc,
        "stdout": stdout,
        "stdout_lines": stdout.splitlines(),
    }
