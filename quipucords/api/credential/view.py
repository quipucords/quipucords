"""Describes the views associated with the API models."""


from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import is_int
from api.exceptions import UnprocessableEntity
from api.filters import ListFilter
from api.models import Credential, Source
from api.serializers import CredentialSerializer
from api.user.authentication import QuipucordsExpiringTokenAuthentication


def related_sources(pk):
    """Return sources related to a credential."""
    return Source.objects.filter(credentials__pk=pk).values("id", "name")


auth_classes = (QuipucordsExpiringTokenAuthentication, SessionAuthentication)
perm_classes = (IsAuthenticated,)


@api_view(["post"])
@authentication_classes(auth_classes)
@permission_classes(perm_classes)
def credential_bulk_delete(request):
    """Bulk delete credentials.

    input:      "ids" : [ ] - List of ids to delete
    returns:    200 OK - upon successfully deleting all credentials.
                400 Bad Request - ids list is missing or empty.
                404 Not Found - If one or more credentials specified do not exist.
                422 Unprocessable Entity - If one or more credentials could
                                           not be deleted.
    """
    ids = request.data.get("ids", [])
    if not ids:
        raise ParseError(detail=_("Missing list of credentials to delete 'ids'"))

    with transaction.atomic():
        try:
            for pk in ids:
                cred = Credential.objects.get(pk=pk)
                if related_sources(pk):
                    raise ValidationError
                cred.delete()
        except Credential.DoesNotExist:
            raise NotFound(detail=_(messages.CRED_ID_DOES_NOT_EXIST % pk))
        except ValidationError:
            raise UnprocessableEntity(
                detail=_(messages.CRED_ID_DELETE_NOT_VALID_W_SOURCES % pk)
            )

    return Response(status=status.HTTP_200_OK)


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

    authentication_classes = (
        QuipucordsExpiringTokenAuthentication,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

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
            sources = related_sources(pk)
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
