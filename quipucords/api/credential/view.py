"""Credential API views."""

from django.utils.translation import gettext as _
from django_filters import CharFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.common.util import set_of_ids_or_all_str
from api.credential.model import Credential, credential_bulk_delete_ids
from api.credential.serializer import (
    AuthTokenOrUserPassSerializerV2,
    AuthTokenSerializerV2,
    CredentialSerializerV2,
    SshCredentialSerializerV2,
    UsernamePasswordSerializerV2,
)
from api.filters import ListFilter
from constants import DataSources


class CredentialFilter(FilterSet):
    """Filter for host credentials by name."""

    name = ListFilter(field_name="name")
    search_by_name = CharFilter(
        field_name="name", lookup_expr="icontains", distinct=True
    )

    class Meta:
        """Metadata for filterset."""

        model = Credential
        fields = ["name", "cred_type", "search_by_name"]


class CredentialViewSetV2(ModelViewSet):
    """A view set for the Credential model."""

    queryset = Credential.objects.prefetch_related("sources")
    # Note: We prefetch the Sources relationship because most queries for Credential
    # also require the related Sources, and prefetching here reduces the cardinality
    # of queries from O(n) to O(1).
    serializer_class = CredentialSerializerV2
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CredentialFilter
    ordering_fields = ("name", "cred_type")
    ordering = ("name",)

    serializer_by_type = {
        DataSources.NETWORK: SshCredentialSerializerV2,
        DataSources.OPENSHIFT: AuthTokenOrUserPassSerializerV2,
        DataSources.VCENTER: UsernamePasswordSerializerV2,
        DataSources.SATELLITE: UsernamePasswordSerializerV2,
        DataSources.ANSIBLE: UsernamePasswordSerializerV2,
        DataSources.RHACS: AuthTokenSerializerV2,
    }

    def get_input_serializer_class(self, cred_type):
        """Get the type-specific serializer for processing create/update inputs."""
        if serializer := self.serializer_by_type.get(cred_type):
            return serializer
        raise ValueError("Invalid credential type.")

    def create(self, request, *args, **kwargs) -> Response:
        """
        Create a credential.

        That this method is based on rest_framework.mixins.CreateModelMixin.create.
        Modifications were made only to use different input and output serializers.
        """
        cred_type = request.data.get("cred_type")
        input_serializer_class = self.get_input_serializer_class(cred_type)

        input_serializer = input_serializer_class(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        instance = input_serializer.save()  # Save the validated data.
        # We are not using `self.perform_create(input_serializer)` here because we need
        # the instance to pass through a different serializer for output.

        # Use the common output serializer for the response.
        output_serializer = self.get_serializer_class()(instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs) -> Response:
        """
        Update a credential.

        That this method is based on rest_framework.mixins.UpdateModelMixin.update.
        Modifications were made only to use different input and output serializers.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        cred_type = request.data.get("cred_type", instance.cred_type)
        input_serializer_class = self.get_input_serializer_class(cred_type)
        input_serializer = input_serializer_class(
            instance, data=request.data, partial=partial
        )
        input_serializer.is_valid(raise_exception=True)
        self.perform_update(input_serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        output_serializer = self.get_serializer_class()(instance)
        return Response(output_serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk_delete")
    def bulk_delete(self, request) -> Response:
        """
        Bulk delete credentials.

        The `ids` POST parameter of the request may be either a list of ids or the
        ALL_IDS_MAGIC_STRING string.

        The returned Response payload contains IDs of credentials deleted, not found,
        and skipped, and a human-readable message describing the overall results,
        and it will have status `200 OK` upon successfully deleting any credentials or
        `400 Bad Request` (ParseError) if the `ids` parameter was missing or empty.

        Example response body:

            {
                "message": \
                    "Deleted 3 credentials. "\
                    "Could not find 0 credentials. "\
                    "Failed to delete 2 credentials.",
                "deleted": [1, 2, 3],
                "missing": [],
                "skipped": [
                    {"credential": 6, "sources": [1]},
                    {"credential": 7, "sources": [2, 3]},
                ],
            }
        """
        ids = set_of_ids_or_all_str(request.data.get("ids"))
        results = credential_bulk_delete_ids(ids)
        message = _(
            "Deleted {count_deleted} credentials. "
            "Could not find {count_missing} credentials. "
            "Failed to delete {count_failed} credentials."
        ).format(
            count_deleted=len(results["deleted"]),
            count_missing=len(results["missing"]),
            count_failed=len(results["skipped"]),
        )
        results["message"] = message
        return Response(data=results, status=status.HTTP_200_OK)
