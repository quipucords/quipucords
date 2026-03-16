"""View for system reports."""

import logging

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from api.insights_report.insights_gzip_renderer import InsightsGzipRenderer
from api.insights_report.payload import generate_insights_payload

logger = logging.getLogger(__name__)


@api_view(["GET"])
@renderer_classes((JSONRenderer, InsightsGzipRenderer, BrowsableAPIRenderer))
def insights(request, report_id=None):
    """Lookup and return an Insights system report."""
    return Response(generate_insights_payload(report_id))
