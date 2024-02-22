"""Defines the models used with the API application.

These models are used in the REST definitions.
"""
import logging

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
DEFAULT_MAX_CONCURRENCY = 25
UPPER_MAX_CONCURRENCY = 200


class Scan(models.Model):
    """Configuration for the scan jobs that will run."""

    SCAN_TYPE_CHOICES = (
        (ScanTask.SCAN_TYPE_CONNECT, ScanTask.SCAN_TYPE_CONNECT),
        (ScanTask.SCAN_TYPE_INSPECT, ScanTask.SCAN_TYPE_INSPECT),
    )

    SUPPORTED_PRODUCTS = ["jboss_eap", "jboss_fuse", "jboss_ws", "jboss_brms"]

    JBOSS_EAP = "jboss_eap"
    JBOSS_EAP_EXT = "jboss_eap_ext"
    EXT_JBOSS_EAP = False
    MODEL_OPT_JBOSS_EAP = True
    EXTRA_VAR_OPT_JBOSS_EAP = MODEL_OPT_JBOSS_EAP

    JBOSS_FUSE = "jboss_fuse"
    JBOSS_FUSE_EXT = "jboss_fuse_ext"
    EXT_JBOSS_FUSE = False
    MODEL_OPT_JBOSS_FUSE = True
    EXTRA_VAR_OPT_JBOSS_FUSE = MODEL_OPT_JBOSS_FUSE

    JBOSS_WS = "jboss_ws"
    JBOSS_WS_EXT = "jboss_ws_ext"
    EXT_JBOSS_WS = False
    MODEL_OPT_JBOSS_WS = True
    EXTRA_VAR_OPT_JBOSS_WS = MODEL_OPT_JBOSS_WS

    JBOSS_BRMS = "jboss_brms"
    JBOSS_BRMS_EXT = "jboss_brms_ext"
    EXT_JBOSS_BRMS = False
    MODEL_OPT_JBOSS_BRMS = True
    EXTRA_VAR_OPT_JBOSS_BRMS = MODEL_OPT_JBOSS_BRMS

    EXT_PRODUCT_SEARCH_DIRS = "search_directories"

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
        scan_options["max_concurrency"] = self.max_concurrency
        if self.enabled_extended_product_search:
            product_search = {}
            enabled_products = self.enabled_extended_product_search
            for prod in Scan.SUPPORTED_PRODUCTS:
                product_search[prod] = enabled_products.get(prod, False)
            search_dir = enabled_products.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None)
            if search_dir is not None:
                product_search[Scan.EXT_PRODUCT_SEARCH_DIRS] = search_dir
            scan_options["enabled_extended_product_search"] = product_search
        if self.enabled_optional_products:
            disabled_products = {}
            for key, val in self.enabled_optional_products.items():
                if val is not None:
                    disabled_products[key] = not val
            scan_options["disabled_optional_products"] = disabled_products
        return scan_options

    @options.setter
    def options(self, value):
        """Implement the v1 compatible Scan options setter."""
        max_concurrency = value.get("max_concurrency", None)
        if max_concurrency is not None:
            self.max_concurrency = convert_to_int(max_concurrency)
        disabled_products = value.get("disabled_optional_products", None)
        if disabled_products is not None:
            enabled_products = {}
            for prod in self.SUPPORTED_PRODUCTS:
                flag = disabled_products.get(prod, None)
                if flag is not None:
                    enabled_products[prod] = not convert_to_boolean(flag)
                else:
                    enabled_products[prod] = True
            self.enabled_optional_products = enabled_products
        extended_search = value.get("enabled_extended_product_search", None)
        if extended_search is not None:
            enabled_extended_product_search = {}
            for prod in Scan.SUPPORTED_PRODUCTS:
                flag = extended_search.get(prod, False)
                enabled_extended_product_search[prod] = convert_to_boolean(flag)
            enabled_extended_product_search[
                Scan.EXT_PRODUCT_SEARCH_DIRS
            ] = extended_search.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None)
            self.enabled_extended_product_search = enabled_extended_product_search

    @staticmethod
    def get_default_forks():
        """Create the default number of forks."""
        return DEFAULT_MAX_CONCURRENCY

    @staticmethod
    def get_max_forks():
        """Create the maximum number of forks."""
        return UPPER_MAX_CONCURRENCY

    @staticmethod
    def get_default_extra_vars():
        """Create the default set of extra_vars.

        :returns: a dictionary representing extra vars
        """
        defaults = {
            Scan.JBOSS_EAP: Scan.EXTRA_VAR_OPT_JBOSS_EAP,
            Scan.JBOSS_FUSE: Scan.EXTRA_VAR_OPT_JBOSS_FUSE,
            Scan.JBOSS_BRMS: Scan.EXTRA_VAR_OPT_JBOSS_BRMS,
            Scan.JBOSS_WS: Scan.EXTRA_VAR_OPT_JBOSS_WS,
            Scan.JBOSS_EAP_EXT: Scan.EXT_JBOSS_EAP,
            Scan.JBOSS_FUSE_EXT: Scan.EXT_JBOSS_FUSE,
            Scan.JBOSS_BRMS_EXT: Scan.EXT_JBOSS_BRMS,
            Scan.JBOSS_WS_EXT: Scan.EXT_JBOSS_WS,
        }
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
                enable_products[self.JBOSS_BRMS]
                or enable_products[self.JBOSS_FUSE]
                or enable_products[self.JBOSS_EAP]
                or enable_products[self.JBOSS_WS]
            )
            extra_vars[self.JBOSS_FUSE] = enable_products[self.JBOSS_FUSE]
            extra_vars[self.JBOSS_BRMS] = enable_products[self.JBOSS_BRMS]
            extra_vars[self.JBOSS_WS] = enable_products[self.JBOSS_WS]

        # Scan for EAP if fuse or brms are in scan
        extended_search = self.enabled_extended_product_search
        if extended_search is not None:
            extra_vars[self.JBOSS_EAP_EXT] = extended_search.get(
                self.JBOSS_EAP, self.EXT_JBOSS_EAP
            )
            extra_vars[self.JBOSS_FUSE_EXT] = extended_search.get(
                self.JBOSS_FUSE, self.EXT_JBOSS_FUSE
            )
            extra_vars[self.JBOSS_BRMS_EXT] = extended_search.get(
                self.JBOSS_BRMS, self.EXT_JBOSS_BRMS
            )
            extra_vars[self.JBOSS_WS_EXT] = extended_search.get(
                self.JBOSS_WS, self.EXT_JBOSS_WS
            )

            # Add search directories if it is not None, not empty
            search_directories = extended_search.get(self.EXT_PRODUCT_SEARCH_DIRS, None)
            if search_directories is not None:
                if isinstance(search_directories, list):
                    search_directories = " ".join(search_directories)
                    extra_vars[self.EXT_PRODUCT_SEARCH_DIRS] = search_directories

        return extra_vars
