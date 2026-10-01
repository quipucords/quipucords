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
        \tArch: x86_64
        \tTags: rhel-7,rhel-7-x86_64
    """,
        """Product:
        \tName: Red Hat Enterprise Linux Server
        \tID: 69
        \tVersion: 7.0
        \tArch: x86_64
        \tTags: rhel-7,rhel-7-x86_64
    """,
    ],
)
def test_success_found_id_and_name(stdout):
    """ID, Name, Version, Arch and Tags match expected format."""
    cmd_output = {"rc": 0, "stdout": stdout}
    expected_fact = [
        {
            "id": "69",
            "name": "Red Hat Enterprise Linux Server",
            "version": "7.0",
            "arch": "x86_64",
            "tags": ["rhel-7", "rhel-7-x86_64"],
        }
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


@pytest.mark.parametrize(
    "arch_line,expected_arch",
    [
        ("\tArch: x86_64", "x86_64"),
        ("\tArch: x86_64,ppc64le", "x86_64,ppc64le"),
        ("\tArch: ", None),
        ("", None),
    ],
)
def test_product_arch(arch_line, expected_arch):
    """Arch is stashed verbatim, and omitted when absent."""
    stdout = f"""Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 7.0
        {arch_line}
    """
    cmd_output = {"rc": 0, "stdout": stdout}
    expected_fact = {
        "id": "69",
        "name": "Red Hat Enterprise Linux Server",
        "version": "7.0",
    }
    if expected_arch:
        expected_fact["arch"] = expected_arch
    assert installed_products.ProcessInstalledProducts.process(cmd_output) == [
        expected_fact
    ]


@pytest.mark.parametrize(
    "tags_line,expected_tags",
    [
        ("\tTags: rhel-9,rhel-9-x86_64", ["rhel-9", "rhel-9-x86_64"]),
        ("\tTags: rhel-9", ["rhel-9"]),
        ("\tTags: rhel-9, rhel-9-x86_64", ["rhel-9", "rhel-9-x86_64"]),
        ("\tTags: rhel-9,,rhel-9-x86_64", ["rhel-9", "rhel-9-x86_64"]),
        ("\tTags: ", None),
        ("", None),
    ],
)
def test_product_tags(tags_line, expected_tags):
    """Tags are split on commas, and omitted when absent."""
    stdout = f"""Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 9.8
        \tArch: x86_64
        {tags_line}
    """
    cmd_output = {"rc": 0, "stdout": stdout}
    expected_fact = {
        "id": "69",
        "name": "Red Hat Enterprise Linux Server",
        "version": "9.8",
        "arch": "x86_64",
    }
    if expected_tags:
        expected_fact["tags"] = expected_tags
    assert installed_products.ProcessInstalledProducts.process(cmd_output) == [
        expected_fact
    ]


def test_success_multiple_products():
    """ID and Name match expected format for multiple products."""
    stdout = """\nProduct:
        \tID: 479
        \tName: Red Hat Enterprise Linux for x86_64
        \tVersion: 8.6
        \tArch: x86_64
        \tTags: rhel-8,rhel-8-x86_64
    --
    Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 8.7
        \tArch: x86_64
        \tTags: rhel-8,rhel-8-x86_64
    --
    Product:
        \tID: 69
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 8.7
        \tArch: x86_64
        \tTags: rhel-8,rhel-8-x86_64
    --
    Product:
        \tID: 81
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 6.6
        \tArch: ppc64le
        \tTags: rhel-6,rhel-6-ppc64le
    --
    Product:
        \tID: 81
        \tName: Red Hat Enterprise Linux Server
        \tVersion: 6.6
        \tArch: ppc64le
        \tTags: rhel-6,rhel-6-ppc64le
    """
    expected_fact = [
        {
            "id": "479",
            "name": "Red Hat Enterprise Linux for x86_64",
            "version": "8.6",
            "arch": "x86_64",
            "tags": ["rhel-8", "rhel-8-x86_64"],
        },
        {
            "id": "69",
            "name": "Red Hat Enterprise Linux Server",
            "version": "8.7",
            "arch": "x86_64",
            "tags": ["rhel-8", "rhel-8-x86_64"],
        },
        {
            "id": "81",
            "name": "Red Hat Enterprise Linux Server",
            "version": "6.6",
            "arch": "ppc64le",
            "tags": ["rhel-6", "rhel-6-ppc64le"],
        },
    ]
    cmd_output = {"rc": 0, "stdout": stdout}
    assert (
        installed_products.ProcessInstalledProducts.process(cmd_output) == expected_fact
    )


def rhel_cert(version, arch="x86_64", product_id="479"):
    """Build a base RHEL product, tagged the way a real cert is."""
    major = version.split(".")[0]
    return {
        "id": product_id,
        "name": "Red Hat Enterprise Linux for x86_64",
        "version": version,
        "arch": arch,
        "tags": [f"rhel-{major}", f"rhel-{major}-{arch}"],
    }


@pytest.mark.parametrize(
    "products,expected_version",
    [
        pytest.param([rhel_cert("9.8")], "9.8", id="base-rhel"),
        pytest.param(
            [rhel_cert("10.1", arch="aarch64", product_id="419")],
            "10.1",
            id="base-rhel-aarch64",
        ),
        pytest.param(
            [
                rhel_cert("9.8"),
                {
                    "id": "83",
                    "name": "Red Hat Enterprise Linux High Availability",
                    "version": "9.8",
                    "arch": "x86_64",
                    "tags": ["rhel-9-highavailability"],
                },
            ],
            "9.8",
            id="add-on-sharing-version-and-arch-is-ignored",
        ),
        pytest.param(
            [
                {
                    "id": "240",
                    "name": "Oracle Java (for RHEL Server)",
                    "version": "1.8",
                    "arch": "x86_64",
                    "tags": ["rhel-7-java"],
                }
            ],
            None,
            id="layered-product-only",
        ),
        pytest.param(
            [rhel_cert("9.8"), rhel_cert("10.2", product_id="486")],
            None,
            id="two-base-certs-disagree",
        ),
        pytest.param([rhel_cert("9.8"), rhel_cert("9.8")], "9.8", id="duplicate-certs"),
        pytest.param(
            [{"id": "479", "name": "Red Hat Enterprise Linux for x86_64"}],
            None,
            id="no-version-or-tags",
        ),
        pytest.param(
            [{"id": "479", "name": "RHEL", "tags": ["rhel-9"]}],
            None,
            id="tags-without-version",
        ),
        pytest.param(
            [{"id": "479", "name": "RHEL", "version": "9.8"}],
            None,
            id="version-without-tags",
        ),
        pytest.param([], None, id="no-products"),
    ],
)
def test_rhel_version(products, expected_version):
    """rhel_version comes from the cert whose bare rhel-<major> tag matches."""
    dependencies = {"installed_products": products}
    assert (
        installed_products.ProcessRhelVersion.process(
            "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
        )
        == expected_version
    )


@pytest.mark.parametrize("dependencies", [{}, {"installed_products": None}, None])
def test_rhel_version_without_installed_products(dependencies):
    """A missing installed_products dependency yields no version, not an error."""
    assert (
        installed_products.ProcessRhelVersion.process(
            "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
        )
        is None
    )


def test_rhel_version_logs_when_certs_disagree(caplog):
    """Conflicting base certs are reported rather than silently resolved."""
    caplog.set_level("WARNING")
    dependencies = {
        "installed_products": [rhel_cert("9.8"), rhel_cert("10.2", product_id="486")]
    }
    assert (
        installed_products.ProcessRhelVersion.process(
            "QUIPUCORDS_FORCE_POST_PROCESS", dependencies
        )
        is None
    )
    assert "product certificates disagree" in caplog.messages[-1]
    assert "['10.2', '9.8']" in caplog.messages[-1]
