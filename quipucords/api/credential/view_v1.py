"""Describes the views associated with the API models."""

import warnings

from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from api import messages
from api.common.util import is_int
from api.filters import ListFilter
from api.models import Credential, Source
from api.serializers import CredentialSerializerV1


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
