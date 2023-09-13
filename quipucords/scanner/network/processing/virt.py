"""Initial processing of the shell output from the virt role."""

from api.common.util import convert_to_int, is_int
from scanner.network.processing import process

VIRT_TYPE_VMWARE = "vmware"
VIRT_TYPE_VIRTUALBOX = "virtualbox"
VIRT_TYPE_VIRTUALPC = "virtualpc"
VIRT_TYPE_KVM = "kvm"
VIRT_TYPE_XEN = "xen"


def is_last_stdout_line_y(stdout_lines: list) -> bool:
    """Return True if the last line of stdout_lines is "Y"."""
    stdout_lines = [line for line in stdout_lines if line]
    return bool(stdout_lines and stdout_lines[-1] == "Y")


class ProcessVirtXenPrivcmdFound(process.Processor):
    """Process the internal_xen_privcmd_found from virt."""

    KEY = "internal_xen_privcmd_found"

    @staticmethod
    def process(output, dependencies):
        """Process internal_xen_privcmd_found output."""
        return is_last_stdout_line_y(output.get("stdout_lines", []))


class ProcessVirtKvmFound(process.Processor):
    """Process the internal_kvm_found from virt."""

    KEY = "internal_kvm_found"

    @staticmethod
    def process(output, dependencies):
        """Process internal_kvm_found output."""
        return is_last_stdout_line_y(output.get("stdout_lines", []))


class ProcessVirtXenGuest(process.Processor):
    """Process the internal_xen_guest from virt."""

    KEY = "internal_xen_guest"

    @staticmethod
    def process(output, dependencies):
        """Process internal_xen_guest output."""
        result = output.get("stdout_lines", [])
        result = [line for line in result if line]
        return bool(result and is_int(result[-1]) and convert_to_int(result[-1]) > 0)


class ProcessSystemManufacturer(process.Processor):
    """Process the internal_sys_manufacturer from virt."""

    KEY = "internal_sys_manufacturer"
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Process internal_sys_manufacturer output."""
        result = output.get("stdout_lines", [])
        result = [line for line in result if line]
        return result[-1] if result else None


class ProcessVirtCpuModelNameKvm(process.Processor):
    """Process the internal_cpu_model_name_kvm from virt."""

    KEY = "internal_cpu_model_name_kvm"

    @staticmethod
    def process(output, dependencies):
        """Process internal_cpu_model_name_kvm output."""
        return is_last_stdout_line_y(output.get("stdout_lines", []))


class ProcessVirtType(process.Processor):
    """Process the virt_type from virt."""

    KEY = "virt_type"
    REQUIRE_DEPS = False
    DEPS = [
        "internal_have_dmidecode",
        "internal_sys_manufacturer",
        "internal_cpu_model_name_kvm",
        "internal_xen_guest",
        "internal_kvm_found",
        "internal_xen_privcmd_found",
    ]

    @staticmethod
    def process(output, dependencies):  # noqa: PLR0911, C901
        """Process virt_type output."""
        if dependencies is not None and bool(dependencies):
            if dependencies.get("internal_have_dmidecode") and dependencies.get(
                "internal_sys_manufacturer"
            ):
                manufacturer = dependencies.get("internal_sys_manufacturer").lower()
                if "vmware" in manufacturer:
                    return VIRT_TYPE_VMWARE
                if "innotek gmbh" in manufacturer:
                    return VIRT_TYPE_VIRTUALBOX
                if "microsoft" in manufacturer:
                    return VIRT_TYPE_VIRTUALPC
                if "qemu" in manufacturer:
                    return VIRT_TYPE_KVM
            if dependencies.get("internal_cpu_model_name_kvm"):
                return VIRT_TYPE_KVM
            if dependencies.get("internal_kvm_found"):
                return VIRT_TYPE_KVM
            if dependencies.get("internal_xen_guest"):
                return VIRT_TYPE_XEN
            if dependencies.get("internal_xen_privcmd_found"):
                return VIRT_TYPE_XEN
        return None


class ProcessVirtVirt(process.Processor):
    """Process the virt_virt from virt."""

    KEY = "virt_virt"
    REQUIRE_DEPS = False
    DEPS = ["internal_kvm_found", "virt_type"]

    @staticmethod
    def process(output, dependencies):
        """Process virt_virt output."""
        if dependencies is not None and bool(dependencies):
            if dependencies.get("internal_kvm_found"):
                return "virt-host"
            if dependencies.get("virt_type"):
                return "virt-guest"
        return None
