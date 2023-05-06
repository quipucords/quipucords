"""Initial processing of the shell output from the installed_products role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)


class ProcessInstalledProducts(process.Processor):
    """Process the installed_products fact."""

    KEY = "installed_products"

    @staticmethod
    def process(output, dependencies=None):
        """Process installed_product fact output."""
        products = []
        installed_products_cmd_output = output.get("stdout", "")
        # since the command is using grep with surrounding context (-C), we expect each
        # result to be delimited by --
        grep_separator = "--"
        for product in installed_products_cmd_output.split(grep_separator):
            product_dict = {}
            for line in product.splitlines():
                if not line.strip():
                    continue
                key, value = line.strip().split(":", 1)
                if key in ["Name", "ID"]:
                    product_dict[key.lower()] = value.strip()
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
