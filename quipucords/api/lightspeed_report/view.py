"""View for system reports."""

import logging

from django.http import Http404, JsonResponse
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.exceptions import NotFound
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from api.exceptions import FailedDependencyError
from api.lightspeed_report.lightspeed_gzip_renderer import LightspeedGzipRenderer
from api.lightspeed_report.payload import generate_lightspeed_payload

logger = logging.getLogger(__name__)


@api_view(["GET"])
@renderer_classes((JSONRenderer, LightspeedGzipRenderer, BrowsableAPIRenderer))
def lightspeed(request, report_id=None):
    """Lookup and return a Lightspeed system report."""
    try:
        payload = generate_lightspeed_payload(report_id)
    except Http404:
        return JsonResponse({"detail": "Not found."}, status=404)
    except (FailedDependencyError, NotFound) as exc:
        return JsonResponse({"detail": str(exc.detail)}, status=exc.status_code)
    return Response(payload)
