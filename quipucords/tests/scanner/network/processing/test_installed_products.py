"""Unit tests for installed_products fact initial processing."""

import pytest

from scanner.network.processing import installed_products


@pytest.mark.parametrize(
    "stdout",
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
def test_success_found_id_and_name(stdout):
    """ID, Name and Version match expected format."""
    cmd_output = {"rc": 0, "stdout": stdout}
    expected_fact = [
        {"id": "69", "name": "Red Hat Enterprise Linux Server", "version": "7.0"}
    ]
    assert (
        installed_products.ProcessInstalledProducts.process(cmd_output) == expected_fact
    )


@pytest.mark.parametrize(
    "stdout",
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
def test_failure_no_relevant_info(caplog, stdout):
    """Output either doesn't match any required info or don't have id."""
    caplog.set_level("ERROR")
    cmd_output = {"rc": 0, "stdout": stdout}
    err_msg = (
        "Unable to parse relevant product information from the following "
        f" input\n{stdout}"
    )
    assert installed_products.ProcessInstalledProducts.process(cmd_output) == []
    assert caplog.messages[-1] == err_msg


@pytest.mark.parametrize(
    "version_line,expected_version",
    [
        ("\tVersion: 9.4.1", "9.4"),
        ("\tVersion: 9", "9"),
        ("\tVersion: ", None),
        ("", None),
    ],
)
def test_product_version(version_line, expected_version):
    """Version is stashed as major.minor, and omitted when absent."""
    stdout = f"""Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        {version_line}
    """
    cmd_output = {"rc": 0, "stdout": stdout}
    expected_fact = {"id": "69", "name": "Red Hat Enterprise Linux Server"}
    if expected_version:
        expected_fact["version"] = expected_version
    assert installed_products.ProcessInstalledProducts.process(cmd_output) == [
        expected_fact
    ]


def test_success_multiple_products():
    """ID and Name match expected format for multiple products."""
    stdout = """\nProduct:
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
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 8.7
    --
    Product:
        \tID: 81
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 6.6
    --
    Product:
        \tID: 81
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 6.6
    """
    expected_fact = [
        {
            "id": "479",
            "name": "Red Hat Enterprise Linux for x86_64",
            "version": "8.6",
        },
        {"id": "69", "name": "Red Hat Enterprise Linux Server", "version": "8.7"},
        {"id": "81", "name": "Red Hat Enterprise Linux Server", "version": "6.6"},
    ]
    cmd_output = {"rc": 0, "stdout": stdout}
    assert (
        installed_products.ProcessInstalledProducts.process(cmd_output) == expected_fact
    )
