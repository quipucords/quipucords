"""Defines the models used with the API application.

These models are used in the REST definitions.
"""

import logging
from collections import namedtuple

from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.common.util import (
    convert_to_boolean,
    convert_to_int,
)
from api.scantask.model import ScanTask
from api.source.model import Source

logger = logging.getLogger(__name__)
PROD_DEF = namedtuple(
    "Product", ["name", "enabled", "ext_name", "ext_enabled", "extra_var_opt"]
)


class Scan(models.Model):
    """Configuration for the scan jobs that will run."""

    SCAN_TYPE_CHOICES = (
        (ScanTask.SCAN_TYPE_CONNECT, ScanTask.SCAN_TYPE_CONNECT),
        (ScanTask.SCAN_TYPE_INSPECT, ScanTask.SCAN_TYPE_INSPECT),
    )

    JBOSS_EAP = "jboss_eap"
    JBOSS_FUSE = "jboss_fuse"
    JBOSS_WS = "jboss_ws"
    JBOSS_BRMS = "jboss_brms"

    PRODUCTS = {
        JBOSS_EAP: PROD_DEF(JBOSS_EAP, True, f"{JBOSS_EAP}_ext", False, True),
        JBOSS_FUSE: PROD_DEF(JBOSS_FUSE, True, f"{JBOSS_FUSE}_ext", False, True),
        JBOSS_WS: PROD_DEF(JBOSS_WS, True, f"{JBOSS_WS}_ext", False, True),
        JBOSS_BRMS: PROD_DEF(JBOSS_BRMS, True, f"{JBOSS_BRMS}_ext", False, True),
    }

    SUPPORTED_PRODUCTS = PRODUCTS.keys()

    EXT_PRODUCT_SEARCH_DIRS = "search_directories"
    MAX_CONCURRENCY = "max_concurrency"
    DISABLED_OPTIONAL_PRODUCTS = "disabled_optional_products"
    ENABLED_EXTENDED_PRODUCT_SEARCH = "enabled_extended_product_search"

    DEFAULT_MAX_CONCURRENCY = 25
    UPPER_MAX_CONCURRENCY = 200

    name = models.CharField(max_length=64, unique=True)
    sources = models.ManyToManyField(Source)
    scan_type = models.CharField(
        max_length=9,
        choices=SCAN_TYPE_CHOICES,
        default=ScanTask.SCAN_TYPE_INSPECT,
    )

    most_recent_scanjob = models.ForeignKey(
        "api.ScanJob", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    max_concurrency = models.PositiveIntegerField(default=DEFAULT_MAX_CONCURRENCY)
    enabled_optional_products = models.JSONField(null=True)
    enabled_extended_product_search = models.JSONField(null=True)

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCANS_MSG)

    @property
    def options(self):
        """Return the v1 compatible Scan options."""
        scan_options = dict()
        scan_options[Scan.MAX_CONCURRENCY] = self.max_concurrency
        if self.enabled_extended_product_search:
            product_search = {}
            enabled_products = self.enabled_extended_product_search
            for prod in Scan.SUPPORTED_PRODUCTS:
                prod_def = Scan.PRODUCTS[prod]
                product_search[prod_def.name] = enabled_products.get(
                    prod_def.name, prod_def.ext_enabled
                )
            search_dir = enabled_products.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None)
            if search_dir is not None:
                product_search[Scan.EXT_PRODUCT_SEARCH_DIRS] = search_dir
            scan_options[Scan.ENABLED_EXTENDED_PRODUCT_SEARCH] = product_search
        if self.enabled_optional_products:
            disabled_products = {}
            for key, val in self.enabled_optional_products.items():
                if val is not None:
                    disabled_products[key] = not val
            scan_options[Scan.DISABLED_OPTIONAL_PRODUCTS] = disabled_products
        return scan_options

    @options.setter
    def options(self, value):
        """Implement the v1 compatible Scan options setter."""
        max_concurrency = value.get(Scan.MAX_CONCURRENCY, None)
        if max_concurrency is not None:
            self.max_concurrency = convert_to_int(max_concurrency)
        disabled_products = value.get(Scan.DISABLED_OPTIONAL_PRODUCTS, None)
        if disabled_products is not None:
            enabled_products = {}
            for prod in self.SUPPORTED_PRODUCTS:
                flag = disabled_products.get(prod, None)
                if flag is not None:
                    enabled_products[prod] = not convert_to_boolean(flag)
                else:
                    enabled_products[prod] = True
            self.enabled_optional_products = enabled_products
        extended_search = value.get(Scan.ENABLED_EXTENDED_PRODUCT_SEARCH, None)
        if extended_search is not None:
            enabled_extended_product_search = {}
            for prod in Scan.SUPPORTED_PRODUCTS:
                flag = extended_search.get(prod, False)
                enabled_extended_product_search[prod] = convert_to_boolean(flag)
            enabled_extended_product_search[Scan.EXT_PRODUCT_SEARCH_DIRS] = (
                extended_search.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None)
            )
            self.enabled_extended_product_search = enabled_extended_product_search

    @staticmethod
    def get_default_extra_vars():
        """Create the default set of extra_vars.

        :returns: a dictionary representing extra vars
        """
        defaults = {}
        for prod in Scan.SUPPORTED_PRODUCTS:
            prod_def = Scan.PRODUCTS[prod]
            defaults[prod_def.name] = prod_def.extra_var_opt
            defaults[prod_def.ext_name] = prod_def.ext_enabled
        return defaults

    def get_search_directories(self):
        """Load JSON search directory."""
        if self.enabled_extended_product_search:
            return self.enabled_extended_product_search.get(
                self.EXT_PRODUCT_SEARCH_DIRS, []
            )
        return []

    def get_extra_vars(self):
        """Construct a dictionary based on the enabled products.

        :param enabled_optional_products: option products config
        for scan.
        :returns: a dictionary representing the updated collection
        status of the optional products to be assigned as the extra
        vars for the ansible task runner
        """
        extra_vars = self.get_default_extra_vars()

        enable_products = self.enabled_optional_products
        if enable_products is not None:
            extra_vars[self.JBOSS_EAP] = (
                enable_products.get(
                    self.JBOSS_BRMS, Scan.PRODUCTS[self.JBOSS_BRMS].enabled
                )
                or enable_products.get(
                    self.JBOSS_FUSE, Scan.PRODUCTS[self.JBOSS_FUSE].enabled
                )
                or enable_products.get(
                    self.JBOSS_EAP, Scan.PRODUCTS[self.JBOSS_EAP].enabled
                )
                or enable_products.get(
                    self.JBOSS_WS, Scan.PRODUCTS[self.JBOSS_WS].enabled
                )
            )
            extra_vars[self.JBOSS_FUSE] = enable_products.get(
                self.JBOSS_FUSE, Scan.PRODUCTS[self.JBOSS_FUSE].enabled
            )
            extra_vars[self.JBOSS_BRMS] = enable_products.get(
                self.JBOSS_BRMS, Scan.PRODUCTS[self.JBOSS_BRMS].enabled
            )
            extra_vars[self.JBOSS_WS] = enable_products.get(
                self.JBOSS_WS, Scan.PRODUCTS[self.JBOSS_WS].enabled
            )

        # Scan for EAP if fuse or brms are in scan
        extended_search = self.enabled_extended_product_search
        if extended_search is not None:
            for prod in Scan.SUPPORTED_PRODUCTS:
                prod_def = Scan.PRODUCTS[prod]
                extra_vars[prod_def.ext_name] = extended_search.get(
                    prod_def.name, prod_def.ext_enabled
                )

            # Add search directories if it is not None, not empty
            search_directories = extended_search.get(self.EXT_PRODUCT_SEARCH_DIRS, None)
            if search_directories is not None:
                if isinstance(search_directories, list):
                    search_directories = " ".join(search_directories)
                    extra_vars[self.EXT_PRODUCT_SEARCH_DIRS] = search_directories

        return extra_vars
