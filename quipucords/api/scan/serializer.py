"""Module for serializing all model object for database storage."""

import json

from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework.serializers import (
    CharField,
    DictField,
    PrimaryKeyRelatedField,
    ValidationError,
)

from api import messages
from api.common.serializer import NotEmptySerializer, ValidStringChoiceField
from api.common.util import (
    check_for_existing_name,
    check_path_validity,
    convert_to_boolean,
    convert_to_int,
    is_boolean,
    is_int,
)
from api.models import Scan, Source
from api.scantask.serializer import SourceField

try:
    JsonExceptionClass = json.decoder.JSONDecodeError
except AttributeError:
    JsonExceptionClass = ValueError


class JobField(PrimaryKeyRelatedField):
    """Representation of the source associated with a scan job."""

    def to_representation(self, value):
        """Create output representation."""
        job = {"id": value.id}
        if value.report_id is not None:
            job["report_id"] = value.report_id
        return job


class ScanSerializer(NotEmptySerializer):
    """Serializer for the Scan model."""

    name = CharField(required=True, read_only=False, max_length=64)
    sources = SourceField(many=True, queryset=Source.objects.all())
    scan_type = ValidStringChoiceField(required=False, choices=Scan.SCAN_TYPE_CHOICES)
    options = DictField(required=False, default={})
    jobs = JobField(required=False, many=True, read_only=True)

    class Meta:
        """Metadata for serializer."""

        model = Scan
        fields = [
            "id",
            "name",
            "sources",
            "scan_type",
            "options",
            "jobs",
            "most_recent_scanjob",
        ]
        read_only_fields = ["most_recent_scanjob"]

    @transaction.atomic
    def create(self, validated_data):
        """Create a scan."""
        name = validated_data.get("name")
        check_for_existing_name(
            Scan.objects, name, _(messages.SCAN_NAME_ALREADY_EXISTS % name)
        )
        scan = super().create(validated_data)
        scan.save()
        return scan

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a scan."""
        # If we ever add optional fields to Scan, we need to
        # add logic here to clear them on full update even if they are
        # not supplied.
        name = validated_data.get("name")
        check_for_existing_name(
            Scan.objects,
            name,
            _(messages.HC_NAME_ALREADY_EXISTS % name),
            search_id=instance.id,
        )

        if not self.partial:
            return self._do_full_update(instance, validated_data)
        return self._do_partial_update(instance, validated_data)

    def _do_full_update(self, instance, validated_data):
        """Perform full update of scan."""
        name = validated_data.pop("name", None)
        options = validated_data.pop("options", None)
        scan_type = validated_data.pop("scan_type", None)
        sources = validated_data.pop("sources", None)

        instance.name = name
        instance.scan_type = scan_type
        instance.sources.set(sources)
        if options:
            instance.options = options
        instance.save()
        return instance

    def _do_partial_update(self, instance, validated_data):
        """Perform partial update of a scan."""
        name = validated_data.pop("name", None)
        scan_type = validated_data.pop("scan_type", None)
        sources = validated_data.pop("sources", None)

        # Update values that are not options
        if name is not None:
            instance.name = name
        if scan_type is not None:
            instance.scan_type = scan_type
        if sources is not None:
            instance.sources.set(sources)

        options = validated_data.pop("options", None)
        if options:
            self.update_options(instance, options)

        instance.save()
        return instance

    @staticmethod
    def validate_sources(sources):
        """Make sure the source is present."""
        if not sources:
            raise ValidationError(_(messages.SJ_REQ_SOURCES))

        return sources

    @staticmethod
    def validate_options(options):
        """Make sure the options specified are valid."""
        if options:
            ScanSerializer.validate_max_concurrency(
                options.get("max_concurrency", None)
            )
            ScanSerializer.validate_disabled_optional_products(
                options.get("disabled_optional_products", None)
            )
            ScanSerializer.validate_enabled_extended_product_search(
                options.get("enabled_extended_product_search", None)
            )
        return options

    @staticmethod
    def validate_max_concurrency(max_concurrency):
        """Validate max_concurrency."""
        if max_concurrency is None:
            return None

        if is_int(max_concurrency):
            max_concurrency_int = convert_to_int(max_concurrency)
            if max_concurrency_int < 1:
                errors = {
                    "max_concurrency": [
                        "Ensure this value is greater than or equal to 1."
                    ]
                }
                raise ValidationError(errors)
            if max_concurrency_int > Scan.get_max_forks():
                errors = {
                    "max_concurrency": [
                        "Ensure this value is less than"
                        f" or equal to {Scan.get_max_forks()}."
                    ]
                }
                raise ValidationError(errors)
        else:
            errors = {"max_concurrency": ["Ensure this value is a positive integer."]}
            raise ValidationError(errors)

        return max_concurrency

    @staticmethod
    def validate_disabled_optional_products(disabled_optional_products):
        """Validate disabled_optional_products."""
        if disabled_optional_products is None:
            return None

        if isinstance(disabled_optional_products, str):
            errors = {
                "disabled_optional_products": {
                    "non_field_errors": [
                        "Invalid data. Expected a dictionary, but got str."
                    ]
                }
            }
            raise ValidationError(errors)

        bad_prods = {}
        for prod in Scan.SUPPORTED_PRODUCTS:
            flag = disabled_optional_products.get(prod, None)
            if flag is not None and is_boolean(flag) is False:
                bad_prods[prod] = ["Must be a valid boolean."]
        if bad_prods:
            errors = {"disabled_optional_products": bad_prods}
            raise ValidationError(errors)

        return disabled_optional_products

    @staticmethod
    def validate_enabled_extended_product_search(enabled_extended_product_search):
        """Validate enabled_extended_product_search."""
        if enabled_extended_product_search is None:
            return None

        if isinstance(enabled_extended_product_search, str):
            errors = {
                "enabled_extended_product_search": {
                    "non_field_errors": [
                        "Invalid data. Expected a dictionary, but got str."
                    ]
                }
            }
            raise ValidationError(errors)

        bad_prods = {}
        for prod in Scan.SUPPORTED_PRODUCTS:
            flag = enabled_extended_product_search.get(prod, None)
            if flag is not None and is_boolean(flag) is False:
                bad_prods[prod] = ["Must be a valid boolean."]
        if bad_prods:
            errors = {"enabled_extended_product_search": bad_prods}
            raise ValidationError(errors)

        ScanSerializer.validate_search_directories(
            enabled_extended_product_search.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None)
        )

        return enabled_extended_product_search

    @staticmethod
    def validate_search_directories(search_directories):
        """Validate search directories."""
        if search_directories is None:
            return None

        search_directories_validation_errors = {
            "enabled_extended_product_search": {
                Scan.EXT_PRODUCT_SEARCH_DIRS: [
                    _(messages.SCAN_OPTIONS_EXTENDED_SEARCH_DIR_NOT_LIST)
                ]
            }
        }

        try:
            search_directories_list = search_directories
            if not isinstance(search_directories_list, list):
                raise ValidationError(search_directories_validation_errors)
            for directory in search_directories_list:
                if not isinstance(directory, str):
                    raise ValidationError(search_directories_validation_errors)
            invalid_paths = check_path_validity(search_directories_list)
            if bool(invalid_paths):
                raise ValidationError(search_directories_validation_errors)
        except JsonExceptionClass as exception:
            raise ValidationError(search_directories_validation_errors) from exception

        return search_directories

    def update_options(self, instance, options):
        """Update the options for the Scan."""
        max_concurrency = options.pop("max_concurrency", None)
        if max_concurrency is not None:
            instance.max_concurrency = max_concurrency

        disabled_products = options.pop("disabled_optional_products", None)
        if disabled_products:
            self.update_optional_products(instance, disabled_products)

        extended_search = options.pop("enabled_extended_product_search", None)
        if extended_search:
            self.update_enabled_extended_product_search(instance, extended_search)

    @staticmethod
    def update_optional_products(instance, disabled_products):
        """Update the enabled_optional_products."""
        optional_products_instance = instance.enabled_optional_products
        if not optional_products_instance:
            # Need to create a new ones
            enabled_optional_products = {}
            for prod in Scan.SUPPORTED_PRODUCTS:
                flag = disabled_products.get(prod, False)
                enabled_optional_products[prod] = not convert_to_boolean(flag)
            instance.enabled_optional_products = enabled_optional_products
        else:
            # Existing values to update
            enabled_optional_products = optional_products_instance
            for prod in Scan.SUPPORTED_PRODUCTS:
                flag = disabled_products.get(prod, None)
                if flag is not None:
                    enabled_optional_products[prod] = not convert_to_boolean(flag)
            instance.enabled_optional_products = enabled_optional_products

    @staticmethod
    def update_enabled_extended_product_search(instance, extended_search):
        """Update the enabled_extended_product_search."""
        extended_search_instance = instance.enabled_extended_product_search
        if not extended_search_instance:
            # Need to create a new ones
            enabled_extended_product_search = {}
            for prod in Scan.SUPPORTED_PRODUCTS:
                flag = extended_search.get(prod, None)
                if flag is not None:
                    enabled_extended_product_search[prod] = convert_to_boolean(flag)
            search_directories = extended_search.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None)
            if search_directories:
                enabled_extended_product_search[
                    Scan.EXT_PRODUCT_SEARCH_DIRS
                ] = search_directories
            instance.enabled_extended_product_search = enabled_extended_product_search
        else:
            # Existing values to update
            for prod in Scan.SUPPORTED_PRODUCTS:
                flag = extended_search.get(prod, None)
                if flag is not None:
                    extended_search_instance[prod] = convert_to_boolean(flag)
            if extended_search.get(Scan.EXT_PRODUCT_SEARCH_DIRS, None) is not None:
                extended_search_instance[
                    Scan.EXT_PRODUCT_SEARCH_DIRS
                ] = extended_search.get(Scan.EXT_PRODUCT_SEARCH_DIRS)
