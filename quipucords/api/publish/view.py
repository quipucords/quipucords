"""Views for publishing reports to consoledot."""

import http

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api import messages
from api.common.lightspeed import get_cannot_publish_reason
from api.models import Report
from api.publish.model import PublishRequest
from api.publish.serializer import PublishRequestSerializer
from api.publish.tasks import request_publish

_PUBLISH_RESPONSE_EXAMPLE = {
    "report_id": 1,
    "status": "pending",
    "error_code": "",
    "error_message": "",
    "created_at": "2026-03-26T18:00:00.000000Z",
    "updated_at": "2026-03-26T18:00:00.000000Z",
}


@extend_schema(
    methods=["GET"],
    responses={
        (200, "application/json"): OpenApiResponse(
            description="Current publish status for the report",
            response=PublishRequestSerializer,
            examples=[
                OpenApiExample(
                    "Completed publish request",
                    value={**_PUBLISH_RESPONSE_EXAMPLE, "status": "sent"},
                ),
                OpenApiExample(
                    "Failed publish request",
                    value={
                        **_PUBLISH_RESPONSE_EXAMPLE,
                        "status": "failed",
                        "error_code": "network_unreachable",
                        "error_message": "Connection error: Connection refused",
                    },
                ),
            ],
        ),
        (404, "application/json"): OpenApiResponse(
            description="Report or publish request not found",
            examples=[
                OpenApiExample(
                    "No publish request",
                    value={"detail": "No publish request found for this report."},
                ),
            ],
        ),
    },
)
@extend_schema(
    methods=["POST"],
    request=None,
    responses={
        (201, "application/json"): OpenApiResponse(
            description="Publish request created",
            response=PublishRequestSerializer,
            examples=[
                OpenApiExample(
                    "Publish request created",
                    value=_PUBLISH_RESPONSE_EXAMPLE,
                ),
            ],
        ),
        (400, "application/json"): OpenApiResponse(
            description="Report cannot be published",
            examples=[
                OpenApiExample(
                    "Not publishable",
                    value={
                        "code": "invalid_report",
                        "message": "Report cannot be published: not_complete",
                    },
                ),
            ],
        ),
        (404, "application/json"): OpenApiResponse(
            description="Report not found",
        ),
        (409, "application/json"): OpenApiResponse(
            description="A publish is already in progress",
            examples=[
                OpenApiExample(
                    "Already pending",
                    value={
                        "code": "already_pending",
                        "message": messages.PUBLISH_ALREADY_PENDING,
                    },
                ),
            ],
        ),
    },
)
@api_view(["GET", "POST"])
def publish_report(request, report_id):
    """Trigger or check the status of a report publish to consoledot."""
    report = get_object_or_404(Report, pk=report_id)

    if request.method == "GET":
        return _get_publish_status(report)
    return _create_publish(report, request.user)


def _get_latest_publish_request(report):
    """Return the most recent PublishRequest for a report, or None."""
    return report.publish_requests.order_by("-created_at").first()


def _get_publish_status(report):
    publish_request = _get_latest_publish_request(report)
    if publish_request is None:
        return Response(
            {"detail": "No publish request found for this report."},
            status=http.HTTPStatus.NOT_FOUND,
        )
    return Response(PublishRequestSerializer(publish_request).data)


def _create_publish(report, user):
    cannot_publish_reason = get_cannot_publish_reason(report, user)
    if cannot_publish_reason is not None:
        return Response(
            {
                "code": PublishRequest.ErrorCode.INVALID_REPORT,
                "message": messages.PUBLISH_NOT_PUBLISHABLE
                % cannot_publish_reason.value,
            },
            status=http.HTTPStatus.BAD_REQUEST,
        )

    existing = _get_latest_publish_request(report)
    if existing and existing.status == PublishRequest.Status.PENDING:
        return Response(
            {
                "code": "already_pending",
                "message": messages.PUBLISH_ALREADY_PENDING,
            },
            status=http.HTTPStatus.CONFLICT,
        )

    publish_request = request_publish(report, user)
    return Response(
        PublishRequestSerializer(publish_request).data,
        status=http.HTTPStatus.CREATED,
    )
