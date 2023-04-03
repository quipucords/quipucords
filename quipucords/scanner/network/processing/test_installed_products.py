"""Unit tests for installed_products fact initial processing."""

import pytest

from scanner.network.processing import installed_products


@pytest.mark.parametrize(
    "stdout_lines",
    [
        """Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 7.0
    """,
        """Product:
        \tName: Red Hat Enterprise Linux Server
        \tID: 69
        \tVersion: 7.0
    """,
    ],
)
def test_success_found_id_and_name(stdout_lines):
    """ID and Name match expected format."""
    cmd_output = {"rc": 0, "stdout_lines": stdout_lines}
    expected_fact = [{"id": "69", "name": "Red Hat Enterprise Linux Server"}]
    assert (
        installed_products.ProcessInstalledProducts.process(cmd_output) == expected_fact
    )


@pytest.mark.parametrize(
    "stdout_lines",
    [
        """Product:
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 7.0
    """,
        """Certificate:
        \tPath: /etc/pki/product/69.pem
        \tVersion: 1.0
        \tCN: Red Hat Product ID [eb3b72ca-acb1-4092-9e67-f2915f6444f4]
    """,
    ],
)
def test_failure_no_relevant_info(caplog, stdout_lines):
    """Output either doesn't match any required info or don't have id."""
    caplog.set_level("ERROR")
    cmd_output = {"rc": 0, "stdout_lines": stdout_lines}
    err_msg = (
        "Unable to parse relevant product information from the following "
        f" input\n{stdout_lines}"
    )
    assert installed_products.ProcessInstalledProducts.process(cmd_output) == []
    assert caplog.messages[-1] == err_msg


def test_success_multiple_products():
    """ID and Name match expected format for multiple products."""
    stdout_lines = """\nProduct:
        \tID: 479
        \tName: Red Hat Enterprise Linux for x86_64
        \tVersion: 8.6
    --
    Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 8.7
    --
    Product:
        \tID: 81
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 6.6
    """
    expected_fact = [
        {"id": "479", "name": "Red Hat Enterprise Linux for x86_64"},
        {"id": "69", "name": "Red Hat Enterprise Linux Server"},
        {"id": "81", "name": "Red Hat Enterprise Linux Server"},
    ]
    cmd_output = {"rc": 0, "stdout_lines": stdout_lines}
    assert (
        installed_products.ProcessInstalledProducts.process(cmd_output) == expected_fact
    )
