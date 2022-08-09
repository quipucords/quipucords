# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

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
