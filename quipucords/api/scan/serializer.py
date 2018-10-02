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
"""Module for serializing all model object for database storage."""

import json


import api.messages as messages
from api.common.serializer import (CustomJSONField,
                                   NotEmptySerializer,
                                   ValidStringChoiceField)
from api.common.util import (check_for_existing_name,
                             check_path_validity)
from api.models import (DisabledOptionalProductsOptions,
                        ExtendedProductSearchOptions,
                        Scan,
                        ScanOptions,
                        Source)
from api.scantask.serializer import SourceField

from django.db import transaction
from django.utils.translation import ugettext as _

from rest_framework.serializers import (BooleanField,
                                        CharField,
                                        IntegerField,
                                        PrimaryKeyRelatedField,
                                        ValidationError)

# pylint: disable=invalid-name
try:
    json_exception_class = json.decoder.JSONDecodeError
except AttributeError:
    json_exception_class = ValueError


class ExtendedProductSearchOptionsSerializer(NotEmptySerializer):
    """The extended production search options of a scan."""

    jboss_eap = BooleanField(required=False)
    jboss_fuse = BooleanField(required=False)
    jboss_brms = BooleanField(required=False)
    jboss_ws = BooleanField(required=False)
    search_directories = CustomJSONField(required=False)

    class Meta:
        """Metadata for serializer."""

        model = ExtendedProductSearchOptions
        fields = ['jboss_eap',
                  'jboss_fuse',
                  'jboss_brms',
                  'jboss_ws',
                  'search_directories']

    @staticmethod
    def validate_search_directories(search_directories):
        """Validate search directories."""
        try:
            search_directories_list = json.loads(search_directories)
            if not isinstance(search_directories_list, list):
                raise ValidationError(
                    _(messages.SCAN_OPTIONS_EXTENDED_SEARCH_DIR_NOT_LIST))
            for directory in search_directories_list:
                if not isinstance(directory, str):
                    raise ValidationError(
                        _(messages.SCAN_OPTIONS_EXTENDED_SEARCH_DIR_NOT_LIST))
            invalid_paths = check_path_validity(search_directories_list)
            if bool(invalid_paths):
                raise ValidationError(
                    _(messages.SCAN_OPTIONS_EXTENDED_SEARCH_DIR_NOT_LIST))
        except json_exception_class:
            raise ValidationError(
                _(messages.SCAN_OPTIONS_EXTENDED_SEARCH_DIR_NOT_LIST))
        return search_directories


class DisableOptionalProductsOptionsSerializer(NotEmptySerializer):
    """The extended production search options of a scan."""

    jboss_eap = BooleanField(required=False)
    jboss_fuse = BooleanField(required=False)
    jboss_brms = BooleanField(required=False)
    jboss_ws = BooleanField(required=False)

    class Meta:
        """Metadata for serializer."""

        model = DisabledOptionalProductsOptions
        fields = ['jboss_eap',
                  'jboss_fuse',
                  'jboss_brms',
                  'jboss_ws']


class ScanOptionsSerializer(NotEmptySerializer):
    """Serializer for the ScanOptions model."""

    max_concurrency = IntegerField(required=False, min_value=1, default=50)
    disabled_optional_products = DisableOptionalProductsOptionsSerializer(
        required=False)
    enabled_extended_product_search = ExtendedProductSearchOptionsSerializer(
        required=False)

    class Meta:
        """Metadata for serializer."""

        model = ScanOptions
        fields = ['max_concurrency',
                  'disabled_optional_products',
                  'enabled_extended_product_search']


class JobField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_representation(self, value):
        """Create output representation."""
        job = {'id': value.id}
        if value.report_id is not None:
            job['report_id'] = value.report_id
        return job


class ScanSerializer(NotEmptySerializer):
    """Serializer for the Scan model."""

    name = CharField(required=True, read_only=False, max_length=64)
    sources = SourceField(many=True, queryset=Source.objects.all())
    scan_type = ValidStringChoiceField(required=False,
                                       choices=Scan.SCAN_TYPE_CHOICES)
    options = ScanOptionsSerializer(required=False, many=False)
    jobs = JobField(required=False, many=True, read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = Scan
        fields = ['id', 'name', 'sources', 'scan_type', 'options', 'jobs',
                  'most_recent_scanjob']
        read_only_fields = ['most_recent_scanjob']

    @transaction.atomic
    def create(self, validated_data):
        """Create a scan."""
        name = validated_data.get('name')
        check_for_existing_name(
            Scan.objects,
            name,
            _(messages.SCAN_NAME_ALREADY_EXISTS % name))

        options = validated_data.pop('options', None)
        scan = super().create(validated_data)

        if options:
            optional_products = options.pop(
                'disabled_optional_products', None)
            extended_search = options.pop(
                'enabled_extended_product_search', None)
            options = ScanOptions.objects.create(**options)
            if optional_products:
                optional_products = \
                    DisabledOptionalProductsOptions.objects.create(
                        **optional_products)
                optional_products.save()
                options.disabled_optional_products = optional_products

            if extended_search:
                extended_search = \
                    ExtendedProductSearchOptions.objects.create(
                        **extended_search)
                extended_search.save()
                options.enabled_extended_product_search = extended_search
            options.save()
            scan.options = options
            scan.save()

        return scan

    # pylint: disable=too-many-locals
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a scan."""
        # If we ever add optional fields to Scan, we need to
        # add logic here to clear them on full update even if they are
        # not supplied.
        # pylint: disable=too-many-statements,too-many-branches
        name = validated_data.get('name')
        check_for_existing_name(
            Scan.objects,
            name,
            _(messages.HC_NAME_ALREADY_EXISTS % name),
            search_id=instance.id)

        name = validated_data.pop('name', None)
        scan_type = validated_data.pop('scan_type', None)
        sources = validated_data.pop('sources', None)
        old_options = instance.options
        options = validated_data.pop('options', None)
        if not self.partial:
            instance.name = name
            instance.scan_type = scan_type
            # clear all the sources and re-add them
            instance.sources.clear()
            for source in sources:
                instance.sources.add(source)
            instance.save()
            if options:
                optional_products = options.pop(
                    'disabled_optional_products', None)
                extended_search = options.pop(
                    'enabled_extended_product_search', None)
                options = ScanOptions.objects.create(**options)
                if optional_products:
                    optional_products = \
                        DisabledOptionalProductsOptions.objects.create(
                            **optional_products)
                    optional_products.save()
                    options.disabled_optional_products = optional_products

                if extended_search:
                    extended_search = \
                        ExtendedProductSearchOptions.objects.create(
                            **extended_search)
                    extended_search.save()
                    options.enabled_extended_product_search = extended_search
                options.save()
                instance.options = options
        else:
            if name is not None:
                instance.name = name
            if scan_type is not None:
                instance.scan_type = scan_type
            if sources is not None:
                instance.sources = sources
            if options is not None:
                # grab the old options
                old_optional_products = old_options.disabled_optional_products
                old_extended_search = \
                    old_options.enabled_extended_product_search
                # set the defaults
                real_extended_search = \
                    {ScanOptions.JBOSS_EAP:
                     ExtendedProductSearchOptions.EXT_JBOSS_EAP,
                     ScanOptions.JBOSS_BRMS:
                     ExtendedProductSearchOptions.EXT_JBOSS_BRMS,
                     ScanOptions.JBOSS_FUSE:
                     ExtendedProductSearchOptions.EXT_JBOSS_FUSE,
                     ScanOptions.JBOSS_WS:
                     ExtendedProductSearchOptions.EXT_JBOSS_WS}
                real_optional_products = \
                    {ScanOptions.JBOSS_EAP:
                     DisabledOptionalProductsOptions.MODEL_OPT_JBOSS_EAP,
                     ScanOptions.JBOSS_BRMS:
                     DisabledOptionalProductsOptions.MODEL_OPT_JBOSS_BRMS,
                     ScanOptions.JBOSS_FUSE:
                     DisabledOptionalProductsOptions.MODEL_OPT_JBOSS_FUSE,
                     ScanOptions.JBOSS_WS:
                     DisabledOptionalProductsOptions.MODEL_OPT_JBOSS_WS}
                # update defaults with old options if they exist
                if old_extended_search:
                    real_extended_search[ScanOptions.JBOSS_EAP] = \
                        old_extended_search.jboss_eap
                    real_extended_search[ScanOptions.JBOSS_BRMS] = \
                        old_extended_search.jboss_brms
                    real_extended_search[ScanOptions.JBOSS_FUSE] = \
                        old_extended_search.jboss_fuse
                    real_extended_search[ScanOptions.JBOSS_WS] = \
                        old_extended_search.jboss_ws
                    if old_extended_search.search_directories:
                        real_extended_search['search_directories'] = \
                            old_extended_search.search_directories
                if old_optional_products:
                    real_optional_products[ScanOptions.JBOSS_EAP] = \
                        old_optional_products.jboss_eap
                    real_optional_products[ScanOptions.JBOSS_BRMS] = \
                        old_optional_products.jboss_brms
                    real_optional_products[ScanOptions.JBOSS_FUSE] = \
                        old_optional_products.jboss_fuse
                    real_optional_products[ScanOptions.JBOSS_WS] = \
                        old_optional_products.jboss_ws
                # grab the new options
                optional_products = options.pop(
                    'disabled_optional_products', None)
                extended_search = options.pop(
                    'enabled_extended_product_search', None)
                if extended_search:
                    # Grab the new extended search options
                    jboss_eap_ext = \
                        extended_search.pop(ScanOptions.JBOSS_EAP, None)
                    jboss_fuse_ext = \
                        extended_search.pop(ScanOptions.JBOSS_FUSE, None)
                    jboss_brms_ext = \
                        extended_search.pop(ScanOptions.JBOSS_BRMS, None)
                    jboss_ws_ext = \
                        extended_search.pop(ScanOptions.JBOSS_WS, None)
                    search_directories = extended_search.pop(
                        'search_directories', None)

                    # for each extended search option, set if provided
                    # else retain the old option
                    if jboss_eap_ext is not None:
                        real_extended_search[ScanOptions.JBOSS_EAP] = \
                            jboss_eap_ext
                    if jboss_brms_ext is not None:
                        real_extended_search[ScanOptions.JBOSS_BRMS] = \
                            jboss_brms_ext
                    if jboss_fuse_ext is not None:
                        real_extended_search[ScanOptions.JBOSS_FUSE] = \
                            jboss_fuse_ext
                    if jboss_ws_ext is not None:
                        real_extended_search[ScanOptions.JBOSS_WS] = \
                            jboss_ws_ext
                    if search_directories is not None:
                        real_extended_search['search_directories'] = \
                            search_directories
                    extended_search = \
                        ExtendedProductSearchOptions.objects.create(
                            **real_extended_search)
                    extended_search.save()

                else:
                    extended_search = old_extended_search

                if optional_products:
                    jboss_eap = \
                        optional_products.pop(ScanOptions.JBOSS_EAP, None)
                    jboss_fuse = \
                        optional_products.pop(ScanOptions.JBOSS_FUSE, None)
                    jboss_brms = \
                        optional_products.pop(ScanOptions.JBOSS_BRMS, None)
                    jboss_ws = \
                        optional_products.pop(ScanOptions.JBOSS_WS, None)

                    if jboss_eap is not None:
                        real_optional_products[ScanOptions.JBOSS_EAP] = \
                            jboss_eap
                    if jboss_brms is not None:
                        real_optional_products[ScanOptions.JBOSS_BRMS] = \
                            jboss_brms
                    if jboss_fuse is not None:
                        real_optional_products[ScanOptions.JBOSS_FUSE] = \
                            jboss_fuse
                    if jboss_ws is not None:
                        real_optional_products[ScanOptions.JBOSS_WS] = \
                            jboss_ws
                    optional_products = \
                        DisabledOptionalProductsOptions.objects.create(
                            **real_optional_products)
                    optional_products.save()
                else:
                    optional_products = old_optional_products
                # create Scan Options for the instance
                instance.options = ScanOptions.objects.create(**options)
                # set the disabled products
                instance.options.disabled_optional_products = \
                    optional_products
                # set the enabled products
                instance.options.enabled_extended_product_search = \
                    extended_search
                instance.options.save()

        instance.save()
        return instance

    @staticmethod
    def validate_sources(sources):
        """Make sure the source is present."""
        if not sources:
            raise ValidationError(_(messages.SJ_REQ_SOURCES))

        return sources
