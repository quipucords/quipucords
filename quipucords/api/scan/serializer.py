#
# Copyright (c) 2018-2019 Red Hat, Inc.
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

from django.db import transaction
from django.utils.translation import ugettext as _

from rest_framework.serializers import (BooleanField,
                                        CharField,
                                        IntegerField,
                                        PrimaryKeyRelatedField,
                                        ValidationError)


from api import messages  # noqa
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

    max_concurrency = IntegerField(required=False, min_value=1,
                                   max_value=200,
                                   default=ScanOptions.get_default_forks())
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

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a scan."""
        # If we ever add optional fields to Scan, we need to
        # add logic here to clear them on full update even if they are
        # not supplied.
        name = validated_data.get('name')
        check_for_existing_name(
            Scan.objects,
            name,
            _(messages.HC_NAME_ALREADY_EXISTS % name),
            search_id=instance.id)

        if not self.partial:
            return self._do_full_update(instance, validated_data)
        return self._do_partial_update(instance, validated_data)

    @staticmethod
    def _do_full_update(instance, validated_data):
        """Peform full update of scan."""
        name = validated_data.pop('name', None)
        scan_type = validated_data.pop('scan_type', None)
        sources = validated_data.pop('sources', None)
        options = validated_data.pop('options', None)

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

        instance.save()
        return instance

    @staticmethod
    def _do_partial_update(instance, validated_data):
        """Peform partial update of a scan."""
        # pylint: disable=too-many-branches,too-many-statements
        name = validated_data.pop('name', None)
        scan_type = validated_data.pop('scan_type', None)
        sources = validated_data.pop('sources', None)

        # Update values that are not options
        if name is not None:
            instance.name = name
        if scan_type is not None:
            instance.scan_type = scan_type
        if sources is not None:
            instance.sources.set(sources)

        options = validated_data.pop('options', None)
        if not options:
            instance.save()
            return instance

        # grab the new options
        optional_products = options.pop(
            'disabled_optional_products', None)
        extended_search = options.pop(
            'enabled_extended_product_search', None)

        # Update base options
        if options:
            options_instance = instance.options
            if not options_instance:
                options_instance = ScanOptions.objects.create(**options)
                options_instance.save()
                instance.options = options_instance
                instance.save()
            else:
                max_concurrency = options.pop('max_concurrency', None)
                if max_concurrency is not None:
                    options_instance.max_concurrency = max_concurrency
                    options_instance.save()

            if not optional_products and not extended_search:
                instance.save()
                return instance
        # Update disable optional products
        if optional_products:
            optional_products_instance = \
                instance.options.disabled_optional_products
            if not optional_products_instance:
                # Need to create a new one
                optional_products_instance = \
                    DisabledOptionalProductsOptions.objects.create(
                        **optional_products)
                optional_products_instance.save()
                instance.options.disabled_optional_products = \
                    optional_products_instance
                instance.options.save()
            else:
                # Existing values so update
                if optional_products.get(
                        ScanOptions.JBOSS_EAP, None) is not None:
                    optional_products_instance.jboss_eap = \
                        optional_products.get(
                            ScanOptions.JBOSS_EAP, None)
                if optional_products.get(
                        ScanOptions.JBOSS_FUSE, None) is not None:
                    optional_products_instance.jboss_fuse = \
                        optional_products.get(
                            ScanOptions.JBOSS_FUSE, None)
                if optional_products.get(
                        ScanOptions.JBOSS_BRMS, None) is not None:
                    optional_products_instance.jboss_brms = \
                        optional_products.get(
                            ScanOptions.JBOSS_BRMS, None)
                if optional_products.get(
                        ScanOptions.JBOSS_WS, None) is not None:
                    optional_products_instance.jboss_ws = \
                        optional_products.get(
                            ScanOptions.JBOSS_WS, None)
                optional_products_instance.save()

        # Update extended product search
        if extended_search:
            extended_search_instance = \
                instance.options.enabled_extended_product_search
            if not extended_search_instance:
                # Create a new one
                extended_search_instance = \
                    ExtendedProductSearchOptions.objects.create(
                        **extended_search)
                extended_search_instance.save()
                instance.options.enabled_extended_product_search = \
                    extended_search_instance
                instance.options.save()
            else:
                # Update existing instance
                # Grab the new extended search options
                if extended_search.get(
                        ScanOptions.JBOSS_EAP, None) is not None:
                    extended_search_instance.jboss_eap = extended_search.get(
                        ScanOptions.JBOSS_EAP, None)

                if extended_search.get(
                        ScanOptions.JBOSS_FUSE, None) is not None:
                    extended_search_instance.jboss_fuse = extended_search.get(
                        ScanOptions.JBOSS_FUSE, None)

                if extended_search.get(
                        ScanOptions.JBOSS_BRMS, None) is not None:
                    extended_search_instance.jboss_brms = extended_search.get(
                        ScanOptions.JBOSS_BRMS, None)

                if extended_search.get(
                        ScanOptions.JBOSS_WS, None) is not None:
                    extended_search_instance.jboss_ws = extended_search.get(
                        ScanOptions.JBOSS_WS, None)
                if extended_search.get(
                        'search_directories', None) is not None:
                    extended_search_instance.search_directories = \
                        extended_search.get(
                            'search_directories', None)
                extended_search_instance.save()

        instance.save()
        return instance

    @staticmethod
    def validate_sources(sources):
        """Make sure the source is present."""
        if not sources:
            raise ValidationError(_(messages.SJ_REQ_SOURCES))

        return sources
