"""Ansible controller scanner."""

# scanner.job expects runners to be importable from scanner module
from .connect import ConnectTaskRunner
from .inspect import InspectTaskRunner
