"""View for server status."""
import os

from django.views.decorators.csrf import csrf_protect
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
    modules,
    platform_info,
    python_version,
    server_version,
)


@api_view(["GET"])
@csrf_protect
@authentication_classes([])
@permission_classes((AllowAny,))
def status(request):
    """Provide the server status information."""
    commit_info = commit()
    server_info = {"api_version": API_VERSION, "server_version": server_version()}
    if commit_info:
        server_info["build"] = commit_info
    server_info["server_address"] = request.META.get("HTTP_HOST", "localhost")
    server_info["platform"] = platform_info()
    server_info["python"] = python_version()
    server_info["modules"] = modules()
    server_info["server_id"] = ServerInformation.create_or_retrieve_server_id()
    env_dict = {}
    for key, value in os.environ.items():
        if "password" not in key.lower():
            env_dict[key] = value
    server_info["environment_vars"] = env_dict
    return Response(server_info)
