"""Initial processing of the shell output from the installed_products role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)


def major_minor_version(version):
    """Reduce a product certificate version to its "major.minor" form."""
    return ".".join(version.split(".")[:2])


def is_rhel_product(product):
    """Check whether a product certificate identifies RHEL itself.

    A base RHEL certificate carries a bare "rhel-<major>" tag matching its own
    version - 479 at version 10.2 is tagged "rhel-10,rhel-10-x86_64". Layered
    and add-on products tag themselves with a qualified variant instead, so the
    bare tag is what tells the operating system apart from what is installed on
    top of it.
    """
    version = product.get("version")
    if not version:
        return False
    major = version.split(".")[0]
    return f"rhel-{major}" in (product.get("tags") or [])


class ProcessInstalledProducts(process.Processor):
    """Process the installed_products fact."""

    KEY = "installed_products"

    @staticmethod
    def process(output, dependencies=None):
        """Process installed_product fact output."""
        products = []
        installed_products_cmd_output = output.get("stdout", "")
        # since the command is using grep with surrounding context (-B/-A), we
        # expect each result to be delimited by --
        grep_separator = "--"
        for product in installed_products_cmd_output.split(grep_separator):
            product_dict = {}
            for line in product.splitlines():
                if not (line.strip() and ":" in line):
                    continue
                key, value = line.strip().split(":", 1)
                if key in ["Name", "ID"]:
                    product_dict[key.lower()] = value.strip()
                elif key == "Version" and value.strip():
                    product_dict["version"] = major_minor_version(value.strip())
                elif key == "Arch" and value.strip():
                    product_dict["arch"] = value.strip()
                elif key == "Tags" and value.strip():
                    product_dict["tags"] = [
                        tag.strip() for tag in value.split(",") if tag.strip()
                    ]
            if not product_dict.get("id"):
                # considering the command includes grep "ID:", if we don't parse product
                # with at least ID, there's an error on the implementation.
                logger.error(
                    "Unable to parse relevant product information from the following "
                    " input\n%s",
                    product,
                )
                continue

            product_id = product_dict["id"]
            if any(p["id"] == product_id for p in products):
                continue
            products.append(product_dict)

        return products


class ProcessRhelVersion(process.Processor):
    """Derive the running RHEL version from the installed product certs."""

    KEY = "rhel_version"
    DEPS = ["installed_products"]
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies=None):
        """Return the version of the product cert identifying RHEL itself."""
        installed_products = (dependencies or {}).get("installed_products") or []
        versions = {
            product["version"]
            for product in installed_products
            if is_rhel_product(product)
        }
        if not versions:
            return None
        if len(versions) > 1:
            # Several certs claim to be the base operating system at different
            # versions. Guessing between them would be worse than admitting we
            # cannot tell, so report nothing and leave a trail to debug with.
            logger.warning(
                "Unable to determine rhel_version: product certificates disagree"
                " on the operating system version %s",
                sorted(versions),
            )
            return None
        return versions.pop()
