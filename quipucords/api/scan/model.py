"""Defines the models used with the API application.

These models are used in the REST definitions.
"""
import logging

from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.scantask.model import ScanTask
from api.source.model import Source

logger = logging.getLogger(__name__)
DEFAULT_MAX_CONCURRENCY = 25


class ExtendedProductSearchOptions(models.Model):
    """The extended production search options of a scan."""

    EXT_JBOSS_EAP = False
    EXT_JBOSS_FUSE = False
    EXT_JBOSS_BRMS = False
    EXT_JBOSS_WS = False
    jboss_eap = models.BooleanField(null=False, default=EXT_JBOSS_EAP)
    jboss_fuse = models.BooleanField(null=False, default=EXT_JBOSS_FUSE)
    jboss_brms = models.BooleanField(null=False, default=EXT_JBOSS_BRMS)
    jboss_ws = models.BooleanField(null=False, default=EXT_JBOSS_WS)
    search_directories = models.JSONField(null=True)

    def __str__(self):
        """Convert to string."""
        return (
            "{"
            f"id:{self.id},"
            f" jboss_eap: {self.jboss_eap},"
            f" jboss_fuse: {self.jboss_fuse},"
            f" jboss_brms: {self.jboss_brms},"
            f" jboss_ws: {self.jboss_ws},"
            f" search_directories: {self.get_search_directories()}"
            "}"
        )

    def get_search_directories(self):
        """Load JSON search directory."""
        return self.search_directories or []


class DisabledOptionalProductsOptions(models.Model):
    """The disable optional products options of a scan."""

    MODEL_OPT_JBOSS_EAP = False
    EXTRA_VAR_OPT_JBOSS_EAP = not MODEL_OPT_JBOSS_EAP

    MODEL_OPT_JBOSS_FUSE = False
    EXTRA_VAR_OPT_JBOSS_FUSE = not MODEL_OPT_JBOSS_FUSE

    MODEL_OPT_JBOSS_BRMS = False
    EXTRA_VAR_OPT_JBOSS_BRMS = not MODEL_OPT_JBOSS_BRMS

    MODEL_OPT_JBOSS_WS = False
    EXTRA_VAR_OPT_JBOSS_WS = not MODEL_OPT_JBOSS_WS

    jboss_eap = models.BooleanField(null=False, default=MODEL_OPT_JBOSS_EAP)
    jboss_fuse = models.BooleanField(null=False, default=MODEL_OPT_JBOSS_FUSE)
    jboss_brms = models.BooleanField(null=False, default=MODEL_OPT_JBOSS_BRMS)
    jboss_ws = models.BooleanField(null=False, default=MODEL_OPT_JBOSS_WS)

    def __str__(self):
        """Convert to string."""
        return (
            "{"
            f"id:{self.id},"
            f" jboss_eap: {self.jboss_eap},"
            f" jboss_fuse: {self.jboss_fuse},"
            f" jboss_brms: {self.jboss_brms},"
            f" jboss_ws: {self.jboss_ws}"
            "}"
        )


class ScanOptions(models.Model):
    """The scan options allows configuration of a scan."""

    JBOSS_EAP = "jboss_eap"
    JBOSS_FUSE = "jboss_fuse"
    JBOSS_BRMS = "jboss_brms"
    JBOSS_WS = "jboss_ws"

    EXT_PRODUCT_SEARCH_DIRS = "search_directories"
    JBOSS_EAP_EXT = "jboss_eap_ext"
    JBOSS_FUSE_EXT = "jboss_fuse_ext"
    JBOSS_BRMS_EXT = "jboss_brms_ext"
    JBOSS_WS_EXT = "jboss_ws_ext"

    max_concurrency = models.PositiveIntegerField(default=DEFAULT_MAX_CONCURRENCY)
    disabled_optional_products = models.OneToOneField(
        DisabledOptionalProductsOptions, on_delete=models.CASCADE, null=True
    )
    enabled_extended_product_search = models.OneToOneField(
        ExtendedProductSearchOptions, on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        """Convert to string."""
        return (
            "{"
            f"id:{self.id},"
            f" max_concurrency: {self.max_concurrency},"
            f" disabled_optional_products: {self.disabled_optional_products},"
            f" enabled_extended_product_search: {self.enabled_extended_product_search}"
            "}"
        )

    @staticmethod
    def get_default_forks():
        """Create the default number of forks."""
        return DEFAULT_MAX_CONCURRENCY

    @staticmethod
    def get_default_extra_vars():
        """Create the default set of extra_vars.

        :returns: a dictionary representing extra vars
        """
        # black likes it this way, but we cross the line length limit,
        # so adding the noqa E501 for keeping pycodestyle happy.
        defaults = {
            ScanOptions.JBOSS_EAP: DisabledOptionalProductsOptions.EXTRA_VAR_OPT_JBOSS_EAP,  # noqa: E501
            ScanOptions.JBOSS_FUSE: DisabledOptionalProductsOptions.EXTRA_VAR_OPT_JBOSS_FUSE,  # noqa: E501
            ScanOptions.JBOSS_BRMS: DisabledOptionalProductsOptions.EXTRA_VAR_OPT_JBOSS_BRMS,  # noqa: E501
            ScanOptions.JBOSS_WS: DisabledOptionalProductsOptions.EXTRA_VAR_OPT_JBOSS_WS,  # noqa: E501
            ScanOptions.JBOSS_EAP_EXT: ExtendedProductSearchOptions.EXT_JBOSS_EAP,
            ScanOptions.JBOSS_FUSE_EXT: ExtendedProductSearchOptions.EXT_JBOSS_FUSE,
            ScanOptions.JBOSS_BRMS_EXT: ExtendedProductSearchOptions.EXT_JBOSS_BRMS,
            ScanOptions.JBOSS_WS_EXT: ExtendedProductSearchOptions.EXT_JBOSS_WS,
        }
        return defaults

    def get_extra_vars(self):
        """Construct a dictionary based on the disabled products.

        :param disabled_optional_products: option products config
        for scan.
        :returns: a dictionary representing the updated collection
        status of the optional products to be assigned as the extra
        vars for the ansibile task runner
        """
        extra_vars = self.get_default_extra_vars()

        disable_products = self.disabled_optional_products
        # when making the disabled products dictionary we have to
        # consider that the roles see True as 'search for product'
        # therefore, we must flip the values from the user to format
        # the extra vars correctly for the role
        if disable_products is not None:
            extra_vars[self.JBOSS_EAP] = not (
                disable_products.jboss_brms
                and disable_products.jboss_fuse
                and disable_products.jboss_eap
                and disable_products.jboss_ws
            )
            extra_vars[self.JBOSS_FUSE] = not disable_products.jboss_fuse
            extra_vars[self.JBOSS_BRMS] = not disable_products.jboss_brms
            extra_vars[self.JBOSS_WS] = not disable_products.jboss_ws

        # Scan for EAP if fuse or brms are in scan
        extended_search = self.enabled_extended_product_search
        if extended_search is not None:
            extra_vars[self.JBOSS_EAP_EXT] = extended_search.jboss_eap
            extra_vars[self.JBOSS_FUSE_EXT] = extended_search.jboss_fuse
            extra_vars[self.JBOSS_BRMS_EXT] = extended_search.jboss_brms
            extra_vars[self.JBOSS_WS_EXT] = extended_search.jboss_ws

            # Add search directories if it is not None, not empty
            if extended_search.search_directories is not None:
                search_directories = extended_search.search_directories
                if search_directories and isinstance(search_directories, list):
                    search_directories = " ".join(search_directories)
                    extra_vars[self.EXT_PRODUCT_SEARCH_DIRS] = search_directories

        return extra_vars


class Scan(models.Model):
    """Configuration for the scan jobs that will run."""

    SCAN_TYPE_CHOICES = (
        (ScanTask.SCAN_TYPE_CONNECT, ScanTask.SCAN_TYPE_CONNECT),
        (ScanTask.SCAN_TYPE_INSPECT, ScanTask.SCAN_TYPE_INSPECT),
    )

    name = models.CharField(max_length=64, unique=True)
    sources = models.ManyToManyField(Source)
    scan_type = models.CharField(
        max_length=9,
        choices=SCAN_TYPE_CHOICES,
        default=ScanTask.SCAN_TYPE_INSPECT,
    )
    options = models.OneToOneField(ScanOptions, null=True, on_delete=models.CASCADE)

    most_recent_scanjob = models.ForeignKey(
        "api.ScanJob", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        """Convert to string."""
        return (
            "{"
            f"id:{self.id},"
            f" name:{self.name},"
            f" sources:{self.sources},"
            f" scan_type:{self.scan_type},"
            f" options: {self.options}"
            "}"
        )

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCANS_MSG)
