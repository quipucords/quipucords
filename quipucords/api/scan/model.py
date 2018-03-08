#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Defines the models used with the API application.

These models are used in the REST definitions.
"""
import logging
import json
from django.utils.translation import ugettext as _
from django.db import models
from api.source.model import Source
from api.scantasks.model import ScanTask
import api.messages as messages

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ExtendedProductSearchOptions(models.Model):
    """The extended production search options of a scan."""

    EXT_JBOSS_EAP = False
    EXT_JBOSS_FUSE = False
    EXT_JBOSS_BRMS = False
    jboss_eap = models.BooleanField(null=False, default=EXT_JBOSS_EAP)
    jboss_fuse = models.BooleanField(null=False, default=EXT_JBOSS_FUSE)
    jboss_brms = models.BooleanField(null=False, default=EXT_JBOSS_BRMS)
    search_directories = models.TextField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'jboss_eap: {}, '\
            'jboss_fuse: {}, '\
            'jboss_brms: {}, '\
            'search_directories:' \
                     ' {}'.format(self.id,
                                  self.jboss_eap,
                                  self.jboss_fuse,
                                  self.jboss_brms,
                                  self.get_search_directories()) + '}'

    def get_search_directories(self):
        """Load JSON search directory."""
        if self.search_directories is not None:
            return json.loads(self.search_directories)
        return []


class DisabledOptionalProductsOptions(models.Model):
    """The disable optional products options of a scan."""

    OPT_JBOSS_EAP = False
    OPT_JBOSS_FUSE = False
    OPT_JBOSS_BRMS = False
    jboss_eap = models.BooleanField(null=False, default=OPT_JBOSS_EAP)
    jboss_fuse = models.BooleanField(null=False, default=OPT_JBOSS_FUSE)
    jboss_brms = models.BooleanField(null=False, default=OPT_JBOSS_BRMS)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'jboss_eap: {}, '\
            'jboss_fuse: {}, '\
            'jboss_brms:' \
                     ' {}'.format(self.id,
                                  self.jboss_eap,
                                  self.jboss_fuse,
                                  self.jboss_brms) + '}'


class ScanOptions(models.Model):
    """The scan options allows configuration of a scan."""

    JBOSS_EAP = 'jboss_eap'
    JBOSS_FUSE = 'jboss_fuse'
    JBOSS_BRMS = 'jboss_brms'

    EXT_PRODUCT_SEARCH_DIRS = 'search_directories'
    JBOSS_EAP_EXT = 'jboss_eap_ext'
    JBOSS_FUSE_EXT = 'jboss_fuse_ext'
    JBOSS_BRMS_EXT = 'jboss_brms_ext'

    max_concurrency = models.PositiveIntegerField(default=50)
    disabled_optional_products = \
        models.ForeignKey(DisabledOptionalProductsOptions,
                          on_delete=models.CASCADE,
                          null=True)
    enabled_extended_product_search = \
        models.ForeignKey(ExtendedProductSearchOptions,
                          on_delete=models.CASCADE, null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'max_concurrency: {}, '\
            'disabled_optional_products: {}, ' \
            'enabled_extended_product_search:' \
                     ' {}'.format(self.id,
                                  self.max_concurrency,
                                  self.disabled_optional_products,
                                  self.enabled_extended_product_search)\
            + '}'

    @staticmethod
    def get_default_forks():
        """Create the default set of extra_vars.

        :returns: a dictionary representing extra vars
        """
        return 50

    @staticmethod
    def get_default_extra_vars():
        """Create the default set of extra_vars.

        :returns: a dictionary representing extra vars
        """
        return {ScanOptions.JBOSS_EAP:
                DisabledOptionalProductsOptions.OPT_JBOSS_EAP,
                ScanOptions.JBOSS_FUSE:
                DisabledOptionalProductsOptions.OPT_JBOSS_FUSE,
                ScanOptions.JBOSS_BRMS:
                DisabledOptionalProductsOptions.OPT_JBOSS_BRMS,
                ScanOptions.JBOSS_EAP_EXT:
                ExtendedProductSearchOptions.EXT_JBOSS_EAP,
                ScanOptions.JBOSS_FUSE_EXT:
                ExtendedProductSearchOptions.EXT_JBOSS_FUSE,
                ScanOptions.JBOSS_BRMS_EXT:
                ExtendedProductSearchOptions.EXT_JBOSS_BRMS}

    def get_extra_vars(self):
        """Construct a dictionary based on the disabled products.

        :param disabled_optional_products: option products config
        for scan.
        :returns: a dictionary representing the updated collection
        status of the optional products to be assigned as the extra
        vars for the ansibile task runner
        """
        extra_vars = self.get_default_extra_vars()
        # pylint: disable=no-member
        disable_products = self.disabled_optional_products
        # when making the disabled products dictionary we have to
        # consider that the roles see True as 'search for product'
        # therefore, we must flip the values from the user to format
        # the extra vars correctly for the role
        if disable_products is not None:
            extra_vars[self.JBOSS_EAP] = \
                not(disable_products.jboss_brms and
                    disable_products.jboss_fuse and
                    disable_products.jboss_eap)
            extra_vars[self.JBOSS_FUSE] = not disable_products.jboss_fuse
            extra_vars[self.JBOSS_BRMS] = not disable_products.jboss_brms
        else:
            extra_vars[self.JBOSS_EAP] = \
                not DisabledOptionalProductsOptions.OPT_JBOSS_EAP
            extra_vars[self.JBOSS_FUSE] = \
                not DisabledOptionalProductsOptions.OPT_JBOSS_FUSE
            extra_vars[self.JBOSS_BRMS] = \
                not DisabledOptionalProductsOptions.OPT_JBOSS_BRMS

        # Scan for EAP if fuse or brms are in scan
        extended_search = self.enabled_extended_product_search
        if extended_search is not None:
            extra_vars[self.JBOSS_EAP_EXT] = extended_search.jboss_eap
            extra_vars[self.JBOSS_FUSE_EXT] = extended_search.jboss_fuse
            extra_vars[self.JBOSS_BRMS_EXT] = extended_search.jboss_brms

            # Add search directories if it is not None, not empty
            if extended_search.search_directories is not None:
                search_directories = json.loads(
                    extended_search.search_directories)
                if search_directories and \
                        isinstance(search_directories, list):
                    search_directories = ' '.join(search_directories)
                    extra_vars[self.EXT_PRODUCT_SEARCH_DIRS] = \
                        search_directories

        return extra_vars


class Scan(models.Model):
    """Configuration for the scan jobs that will run."""

    name = models.CharField(max_length=64, unique=True)
    sources = models.ManyToManyField(Source)
    scan_type = models.CharField(
        max_length=9,
        choices=ScanTask.SCAN_TYPE_CHOICES,
        default=ScanTask.SCAN_TYPE_INSPECT,
    )
    options = models.ForeignKey(
        ScanOptions, null=True, on_delete=models.CASCADE)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'name:{}, '\
            'sources:{}, '\
            'scan_type:{}, '\
            'options: {}'.format(self.id,
                                 self.name,
                                 self.sources,
                                 self.scan_type,
                                 self.options) + '}'

    class Meta:
        """Metadata for model."""

        verbose_name_plural = _(messages.PLURAL_SCAN_JOBS_MSG)
