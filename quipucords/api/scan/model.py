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


class ScanOptions(models.Model):
    """The scan options allows configuration of a scan."""

    JBOSS_EAP = 'jboss_eap'
    JBOSS_FUSE = 'jboss_fuse'
    JBOSS_BRMS = 'jboss_brms'

    max_concurrency = models.PositiveIntegerField(default=50)
    disable_optional_products = models.TextField(null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'max_concurrency: {}, '\
            'disable_optional_products:' \
                     ' {}'.format(self.id,
                                  self.max_concurrency,
                                  self.disable_optional_products)\
            + '}'

    @staticmethod
    def get_extra_vars(disable_optional_products):
        """Construct a dictionary based on the disabled products.

        :param disable_optional_products: option products config
        for scan.
        :returns: a dictionary representing the updated collection
        status of the optional products to be assigned as the extra
        vars for the ansibile task runner
        """
        # Grab the optional products status dict and create
        # a default dict (all products default to True)
        product_status = ScanOptions.get_optional_products(
            disable_optional_products)
        product_default = {ScanOptions.JBOSS_EAP: True,
                           ScanOptions.JBOSS_FUSE: True,
                           ScanOptions.JBOSS_BRMS: True}

        if product_status == {}:
            return product_default
        # If specified, turn off fact collection for fuse
        if product_status.get(ScanOptions.JBOSS_FUSE) is False:
            product_default[ScanOptions.JBOSS_FUSE] = False
        # If specified, turn off fact collection for brms
        if product_status.get(ScanOptions.JBOSS_BRMS) is False:
            product_default[ScanOptions.JBOSS_BRMS] = False
        # If specified and both brms & fuse are false
        # turn off fact collection for eap
        if product_status.get(ScanOptions.JBOSS_EAP) is False and \
                (not product_default.get(ScanOptions.JBOSS_FUSE)) and \
                (not product_default.get(ScanOptions.JBOSS_BRMS)):
            product_default[ScanOptions.JBOSS_EAP] = False

        return product_default

    @staticmethod
    def get_optional_products(disable_optional_products):
        """Access disabled_optional_products as a dict instead of a string.

        :returns: python dict containing the status of optional products
        """
        if disable_optional_products is not None:
            if isinstance(disable_optional_products, dict):
                return disable_optional_products
            return json.loads(disable_optional_products)
        return {}


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
