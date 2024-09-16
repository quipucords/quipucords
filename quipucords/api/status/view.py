"""View for server status."""

from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api import API_VERSION
from api.status.model import ServerInformation
from quipucords.environment import (
    commit,
    platform_info,
    python_version,
    server_version,
)


@api_view(["GET"])
def status(request):
    """Provide the server status information."""
    commit_info = commit()
    server_info = {"api_version": API_VERSION, "server_version": server_version()}
    if commit_info:
        server_info["build"] = commit_info
    server_info["server_address"] = request.META.get("HTTP_HOST", "localhost")
    server_info["platform"] = platform_info()
    server_info["python"] = python_version()
    server_info["server_id"] = ServerInformation.create_or_retrieve_server_id()
    return Response(server_info)


@api_view(["GET"])
@authentication_classes([])
@permission_classes((AllowAny,))
def ping(_request):
    """Provide the public ping endpoint."""
    return HttpResponse("pong", content_type="text/plain")
