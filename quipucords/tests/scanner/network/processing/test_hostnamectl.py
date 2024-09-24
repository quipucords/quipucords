"""Test hostnamectl processing."""

import json
from textwrap import dedent

import pytest
from django.conf import settings

from scanner.network.processing import hostnamectl
from scanner.network.processing.process import ProcessedResult
from tests.scanner.network.processing.util_for_test import ansible_result

hostnamectl_files_dir = settings.BASE_DIR / "testdata" / "hostnamectl-status"


def test_hostnamectl_process_success():
    """Test hostnamectl processing a normal successful response."""
    # Static example taken from a real Fedora 40 VM.
    stdout = dedent("""
                     Static hostname: fedora40
                   Icon name: computer-vm
                     Chassis: vm 🖴
                  Machine ID: ed499cf22ef60b80cd6b80ef64b23e8d
                     Boot ID: e1ba065648b12324be4544c3fa27b71b
              Virtualization: qemu
            Operating System: Fedora Linux 40 (Server Edition)
                 CPE OS Name: cpe:/o:fedoraproject:fedora:40
              OS Support End: Tue 2025-05-13
        OS Support Remaining: 10month 2w 2d
                      Kernel: Linux 6.9.4-200.fc40.x86_64
                Architecture: x86-64
             Hardware Vendor: QEMU
              Hardware Model: Standard PC _Q35 + ICH9, 2009_
            Firmware Version: 0.0.0
               Firmware Date: Fri 2015-02-06
                Firmware Age: 9y 4month 2w 4d
        """)
    exit_code = 0
    result = hostnamectl.ProcessHostnameCTL.process(ansible_result(stdout, exit_code))

    assert result.return_code == exit_code
    assert result.error_msg is None

    # Just spot check a few values that may be useful later for fingerprinting.
    # `test_hostnamectl_process_real_examples` more exhaustively tests all known values.
    assert result.value["architecture"] == "x86-64"
    assert result.value["chassis"] == "vm"
    assert result.value["machine_id"] == "ed499cf22ef60b80cd6b80ef64b23e8d"
    assert result.value["operating_system"] == "Fedora Linux 40 (Server Edition)"
    assert result.value["static_hostname"] == "fedora40"
    assert result.value["virtualization"] == "qemu"


def test_hostnamectl_process_failure():
    """Test hostnamectl processing when the command failed on the target."""
    stdout = "bash: hostnamectl: command not found"
    exit_code = 127
    result = hostnamectl.ProcessHostnameCTL.process(ansible_result(stdout, exit_code))

    assert result.return_code == exit_code
    assert stdout in result.error_msg


@pytest.mark.parametrize(
    "filename,exit_code",
    (
        ("amazon-arm64-amazon-2023.4", 0),
        ("amazon-arm64-rhel-8.4", 0),
        ("amazon-arm64-rhel-9.2", 0),
        ("amazon-x86-64-rhel-7.6", 0),
        ("container-x86-64-rhel-9.2", 0),
        ("kvm-x86-64-centos-7", 0),
        ("kvm-x86-64-centos-stream-8", 0),
        ("kvm-x86-64-rhel-6", 127),  # Non-zero because RHEL6 does not have hostnamectl.
        ("kvm-x86-64-rhel-7.9", 0),
        ("kvm-x86-64-rhel-8.9", 0),
        ("physical-arm-raspbian-10", 0),
        ("physical-x64-64-fedora-40", 0),
        ("physical-x86-64-popos-22.04", 0),
        ("physical-x86-64-truenas-11", 0),
        ("physical-x86-debian-12", 0),
        ("qemu-x86-64-fedora-40", 0),
        ("qemu-x86-64-rhel-9.1", 0),
    ),
)
def test_hostnamectl_process_real_examples(filename: str, exit_code: int):
    """
    Test hostnamectl processing real-world examples.

    The contents of the static test files were captured from several real systems,
    but their IDs and hostnames were anonymized before adding them to this repo.
    """
    with (hostnamectl_files_dir / f"{filename}.txt").open("r") as file:
        raw_response = file.read()
    with (hostnamectl_files_dir / f"{filename}.json").open("r") as file:
        expected_result = ProcessedResult(**json.load(file))

    actual_result = hostnamectl.ProcessHostnameCTL.process(
        ansible_result(raw_response, rc=exit_code)
    )
    assert actual_result == expected_result
