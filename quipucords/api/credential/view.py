"""Describes the views associated with the API models."""
from itertools import groupby

from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import DELETE_ALL_IDS_MAGIC_STRING, is_int
from api.filters import ListFilter
from api.models import Credential, Source
from api.serializers import CredentialSerializer


@api_view(["post"])
def credential_bulk_delete(request):
    """Bulk delete credentials.

    input:      "ids" : List of ids to delete, or string DELETE_ALL_IDS_MAGIC_STRING
    returns:    200 OK - upon successfully deleting all credentials.
                400 Bad Request - ids list is missing or empty.
                404 Not Found - If one or more credentials specified do not exist.
                422 Unprocessable Entity - If one or more credentials could
                                           not be deleted.
    """
    ids = request.data.get("ids")
    if (
        not isinstance(ids, (list, str))
        or (isinstance(ids, str) and ids != DELETE_ALL_IDS_MAGIC_STRING)
        or (isinstance(ids, list) and len(ids) == 0)
        or (isinstance(ids, list) and any([not isinstance(_id, int) for _id in ids]))
    ):
        raise ParseError(
            detail=_(
                "Missing 'ids' list of credential ids "
                "or '{DELETE_ALL_IDS_MAGIC_STRING}' string"
            ).format(DELETE_ALL_IDS_MAGIC_STRING=DELETE_ALL_IDS_MAGIC_STRING)
        )
    elif not isinstance(ids, str):
        ids = set(ids)  # remove duplicates

    with transaction.atomic():
        creds = Credential.objects.all()
        if ids != DELETE_ALL_IDS_MAGIC_STRING:
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


class CredentialFilter(FilterSet):
    """Filter for host credentials by name."""

    name = ListFilter(field_name="name")
    search_by_name = CharFilter(
        field_name="name", lookup_expr="contains", distinct=True
    )

    class Meta:
        """Metadata for filterset."""

        model = Credential
        fields = ["name", "cred_type", "search_by_name"]


class CredentialViewSet(ModelViewSet):
    """A view set for the Credential model."""

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CredentialFilter
    ordering_fields = ("name", "cred_type")
    ordering = ("name",)

    def retrieve(self, request, pk=None):
        """Get a host credential."""
        if not pk or not is_int(pk):
            error = {"id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)
        return super().retrieve(request, pk=pk)

    @transaction.atomic
    def destroy(self, request, pk):
        """Delete a cred."""
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
