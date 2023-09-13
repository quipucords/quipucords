"""Initial processing of the shell output from the cloud_provider role."""

from scanner.network.processing import process

AMAZON = "aws"
GCP = "gcp"
AZURE = "azure"
ALIBABA = "alibaba"


class ProcessDmiChassisAssetTag(process.Processor):
    """Process the dmi chassis asset tag."""

    KEY = "dmi_chassis_asset_tag"

    DEPS = ["internal_dmi_chassis_asset_tag"]
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        dmi_chassis_asset_tag = dependencies.get("internal_dmi_chassis_asset_tag")
        if dmi_chassis_asset_tag and dmi_chassis_asset_tag.get("rc") == 0:
            result = dmi_chassis_asset_tag.get("stdout_lines")
            if result:
                if result[0] == "" and len(result) > 1:  # noqa: PLC1901
                    return result[1]
                return result[0]
        return ""


class ProcessDmiSystemProductName(process.Processor):
    """Process the dmi system product name."""

    KEY = "dmi_system_product_name"

    DEPS = ["internal_dmi_system_product_name"]
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        dmi_system_product_name = dependencies.get("internal_dmi_system_product_name")
        if dmi_system_product_name and dmi_system_product_name.get("rc") == 0:
            result = dmi_system_product_name.get("stdout_lines")
            if result:
                if result[0] == "" and len(result) > 1:  # noqa: PLC1901
                    return result[1].strip()
                return result[0].strip()
        return ""


class ProcessCloudProvider(process.Processor):
    """Process the cloud_provider fact based on dmidecode facts."""

    KEY = "cloud_provider"

    DEPS = [
        "dmi_bios_version",
        "dmi_chassis_asset_tag",
        "dmi_system_manufacturer",
        "dmi_system_product_name",
    ]
    # google & amazon are detected from dmi_bios_version
    # azure is detected from the dmi.chassis.asset_tag
    # alibaba is detected from dmi.system.manufacturer
    # &/OR dmi.system.product_name
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        dmi_bios_version = dependencies.get("dmi_bios_version", "")
        dmi_chassis_asset_tag = dependencies.get("dmi_chassis_asset_tag", "")
        dmi_system_manufacturer = dependencies.get("dmi_system_manufacturer", "")
        dmi_system_product_name = dependencies.get("dmi_system_product_name", "")
        if "amazon" in dmi_bios_version.lower():
            return AMAZON
        if "google" in dmi_bios_version.lower():
            return GCP
        if "7783-7084-3265-9085-8269-3286-77" in dmi_chassis_asset_tag:
            return AZURE
        if (
            "alibaba cloud" in dmi_system_manufacturer.lower()
            or "alibaba cloud ecs" in dmi_system_product_name.lower()
        ):
            return ALIBABA
        return ""
