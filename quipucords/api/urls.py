"""Describes the urls and patterns for the API application."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.aggregate_report.view import aggregate_report
from api.scan.view import scan_bulk_delete
from api.views import (
    CredentialViewSetV1,
    CredentialViewSetV2,
    QuipucordsExpiringAuthTokenView,
    ScanJobViewSet,
    ScanJobViewSetV1,
    ScanViewSet,
    SourceViewSet,
    UserViewSet,
    async_merge_reports,
    credential_bulk_delete,
    deployments,
    details,
    insights,
    jobs,
    ping,
    reports,
    status,
    upload_raw_facts,
)

ROUTER_V1 = SimpleRouter()
ROUTER_V1.register(r"credentials", CredentialViewSetV1, basename="credentials")
ROUTER_V1.register(r"sources", SourceViewSet, basename="source")
ROUTER_V1.register(r"scans", ScanViewSet, basename="scan")
ROUTER_V1.register(r"jobs", ScanJobViewSetV1, basename="scanjob")
ROUTER_V1.register(r"users", UserViewSet, basename="users")

ROUTER_V2 = SimpleRouter()
ROUTER_V2.register(r"credentials", CredentialViewSetV2, basename="credentials")
ROUTER_V2.register(r"sources", SourceViewSet, basename="source")
ROUTER_V2.register(r"jobs", ScanJobViewSet, basename="job")


v1_urls = [
    path(
        "credentials/bulk_delete/",
        credential_bulk_delete,
        name="credentials-bulk-delete",
    ),
    path("scans/bulk_delete/", scan_bulk_delete, name="scans-bulk-delete"),
    path("reports/", upload_raw_facts, name="reports-upload"),
    path(
        "reports/<int:report_id>/aggregate/", aggregate_report, name="reports-aggregate"
    ),
    path("reports/<int:report_id>/details/", details, name="reports-details"),
    path(
        "reports/<int:report_id>/deployments/", deployments, name="reports-deployments"
    ),
    path("reports/<int:report_id>/insights/", insights, name="reports-insights"),
    path("reports/<int:report_id>/", reports, name="reports-detail"),
    path("reports/merge/", async_merge_reports, name="reports-merge"),
    path("scans/<int:scan_id>/jobs/", jobs, name="scan-filtered-jobs"),
    path("token/", QuipucordsExpiringAuthTokenView, name="token"),
    path("status/", status, name="server-status"),
    path("ping/", ping, name="server-ping"),
    *ROUTER_V1.urls,
]

v2_urls = [
    *ROUTER_V2.urls,
]

urlpatterns = [
    path("v1/", include((v1_urls, "api"), namespace="v1")),
    path("v2/", include((v2_urls, "api"), namespace="v2")),
]
