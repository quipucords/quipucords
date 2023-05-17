"""Describes the views associated with the API models."""


from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import is_int
from api.filters import ListFilter
from api.models import Credential, Source
from api.serializers import CredentialSerializer
from api.user.authentication import QuipucordsExpiringTokenAuthentication


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


# pylint: disable=too-many-ancestors
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

    def retrieve(self, request, pk=None):  # pylint: disable=arguments-differ
        """Get a host credential."""
        if not pk or not is_int(pk):
            error = {"id": [_(messages.COMMON_ID_INV)]}
            raise ValidationError(error)
        return super().retrieve(request, pk=pk)

    @transaction.atomic
    def destroy(self, request, pk):  # pylint: disable=arguments-differ
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
