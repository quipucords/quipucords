"""Describes the views associated with the API models."""

import warnings

from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import is_int, set_of_ids_or_all_str
from api.credential.model import credential_bulk_delete_ids
from api.credential.view import CredentialFilter
from api.models import Credential, Source
from api.serializers import CredentialSerializerV1

CREDENTIAL_V1_DEPRECATION_MESSAGE = (
    "The credential v1 API is deprecated and will be removed soon. "
    "Please use the v2 API."
)


class CredentialViewSetV1(ModelViewSet):
    """A view set for the Credential model."""

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializerV1
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CredentialFilter
    ordering_fields = ("name", "cred_type")
    ordering = ("name",)

    def list(self, request, *args, **kwargs):
        """List credentials."""
        warnings.warn(CREDENTIAL_V1_DEPRECATION_MESSAGE, DeprecationWarning)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None):
        """Get a host credential."""
        warnings.warn(CREDENTIAL_V1_DEPRECATION_MESSAGE, DeprecationWarning)
        if not pk or not is_int(pk):
            error = {"id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)
        return super().retrieve(request, pk=pk)

    @transaction.atomic
    def destroy(self, request, pk):
        """Delete a cred."""
        warnings.warn(CREDENTIAL_V1_DEPRECATION_MESSAGE, DeprecationWarning)
        try:
            cred = Credential.objects.get(pk=pk)
            sources = Source.objects.filter(credentials__pk=pk).values("id", "name")
            if sources:
                message = messages.CRED_DELETE_NOT_VALID_W_SOURCES
                error = {"detail": message}
                slim_sources = []
                for source in sources:
                    slim_sources.append(source)
                error["sources"] = slim_sources
                raise ValidationError(error)
            cred.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Credential.DoesNotExist as exception:
            raise Http404 from exception


@api_view(["post"])
def credential_bulk_delete(request) -> Response:
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
    warnings.warn(CREDENTIAL_V1_DEPRECATION_MESSAGE, DeprecationWarning)

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
