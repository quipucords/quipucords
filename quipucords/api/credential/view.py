"""Credential API views."""

from itertools import groupby

from django.db import transaction
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.common.util import ALL_IDS_MAGIC_STRING, set_of_ids_or_all_str
from api.credential.model import Credential
from api.credential.serializer import (
    AuthTokenOrUserPassSerializerV2,
    AuthTokenSerializerV2,
    CredentialSerializerV2,
    SshCredentialSerializerV2,
    UsernamePasswordSerializerV2,
)
from api.credential.view_v1 import CredentialFilter
from constants import DataSources


@api_view(["post"])
def credential_bulk_delete(request):
    """
    Bulk delete credentials.

    Response payload contains IDs of credentials deleted, skipped, and not found.
    Example response:

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

    input:      "ids" : List of ids to delete, or string ALL_IDS_MAGIC_STRING
    returns:    200 OK - upon successfully deleting any credentials.
                400 Bad Request - ids list is missing or empty.
    """
    ids = set_of_ids_or_all_str(request.data.get("ids"))

    with transaction.atomic():
        creds = Credential.objects.all()
        if ids != ALL_IDS_MAGIC_STRING:
            creds = creds.filter(id__in=ids)
        credential_ids_requested = ids if isinstance(ids, set) else set()
        credential_ids_found = set(creds.values_list("id", flat=True))
        credential_ids_with_sources = (
            creds.exclude(sources=None)
            .prefetch_related("sources")
            .values_list("id", "sources")
            .order_by("id")  # later groupby needs sorted input
        )
        creds.filter(sources=None).delete()

    credential_ids_missing = credential_ids_requested - credential_ids_found
    credential_ids_skipped = []

    for credential_id, grouper in groupby(
        credential_ids_with_sources, key=lambda c: c[0]
    ):
        credential_ids_skipped.append(
            {
                "credential": credential_id,
                "sources": [g[1] for g in grouper],
            }
        )
    credential_ids_deleted = credential_ids_found - set(
        c["credential"] for c in credential_ids_skipped
    )

    message = _(
        "Deleted {count_deleted} credentials. "
        "Could not find {count_missing} credentials. "
        "Failed to delete {count_failed} credentials."
    ).format(
        count_deleted=len(credential_ids_deleted),
        count_missing=len(credential_ids_missing),
        count_failed=len(credential_ids_skipped),
    )
    response_data = {
        "message": message,
        "deleted": credential_ids_deleted,
        "missing": credential_ids_missing,
        "skipped": credential_ids_skipped,
    }
    return Response(data=response_data, status=status.HTTP_200_OK)


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
