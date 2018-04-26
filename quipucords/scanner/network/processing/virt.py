# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the cpu role."""

from scanner.network.processing import process


# pylint: disable=too-few-public-methods


class ProcessVirtCpuModelNameKvm(process.Processor):
    """Process the virt_cpu_model_name_kvm from virt."""

    KEY = 'virt_cpu_model_name_kvm'

    @staticmethod
    def process(output, dependencies):
        """Process virt_cpu_model_name_kvm output."""
        result = output
        return result


class ProcessSystemManufacturer(process.Processor):
    """Process the virt_sys_manufacturer from virt."""

    KEY = 'virt_sys_manufacturer'
    REQUIRE_DEPS = False
    DEPS = ['have_dmidecode']

    @staticmethod
    def process(output, dependencies):
        """Process virt_sys_manufacturer output."""
        result = output
        return result


class ProcessVirtXenGuest(process.Processor):
    """Process the virt_xen_guest from virt."""

    KEY = 'virt_xen_guest'

    @staticmethod
    def process(output, dependencies):
        """Process virt_xen_guest output."""
        result = output
        return result


class ProcessVirtKvmFound(process.Processor):
    """Process the virt_kvm_found from virt."""

    KEY = 'virt_kvm_found'

    @staticmethod
    def process(output, dependencies):
        """Process virt_kvm_found output."""
        result = output
        return result


class ProcessVirtXenPrivcmdFound(process.Processor):
    """Process the virt_xen_privcmd_found from virt."""

    KEY = 'virt_xen_privcmd_found'

    @staticmethod
    def process(output, dependencies):
        """Process virt_xen_privcmd_found output."""
        result = output
        return result


class ProcessVirtType(process.Processor):
    """Process the virt_type from virt."""

    KEY = 'virt_type'
    REQUIRE_DEPS = False
    DEPS = ['have_dmidecode',
            'virt_sys_manufacturer',
            'virt_cpu_model_name_kvm',
            'virt_xen_guest',
            'virt_kvm_found',
            'virt_xen_privcmd_found']

    @staticmethod
    def process(output, dependencies):
        """Process virt_type output."""
        result = output
        return result


class ProcessVirtVirt(process.Processor):
    """Process the virt_virt from virt."""

    KEY = 'virt_virt'
    REQUIRE_DEPS = False
    DEPS = ['virt_type']

    @staticmethod
    def process(output, dependencies):
        """Process virt_virt output."""
        result = output
        return result
