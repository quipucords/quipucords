"""Describes the urls and patterns for the API application."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import (
    CredentialViewSet,
    DetailsReportsViewSet,
    QuipucordsExpiringAuthTokenView,
    ScanJobViewSet,
    ScanViewSet,
    SourceViewSet,
    UserViewSet,
    async_merge_reports,
    credential_bulk_delete,
    deployments,
    details,
    insights,
    jobs,
    reports,
    status,
)

ROUTER = SimpleRouter()

ROUTER.register(r"credentials", CredentialViewSet, basename="credentials")
ROUTER.register(r"reports", DetailsReportsViewSet, basename="reports")
ROUTER.register(r"sources", SourceViewSet, basename="source")
ROUTER.register(r"scans", ScanViewSet, basename="scan")
ROUTER.register(r"jobs", ScanJobViewSet, basename="scanjob")
ROUTER.register(r"users", UserViewSet, basename="users")

ROUTER_V2 = SimpleRouter()
ROUTER_V2.register(r"sources", SourceViewSet, basename="source")

v1_urls = [
    path(
        "credentials/bulk_delete/",
        credential_bulk_delete,
        name="credentials-bulk-delete",
    ),
    path("reports/<int:report_id>/details/", details, name="reports-details"),
    path(
        "reports/<int:report_id>/deployments/", deployments, name="reports-deployments"
    ),
    path("reports/<int:report_id>/insights/", insights, name="reports-insights"),
    path("reports/<int:report_id>/", reports, name="reports-detail"),
    path("reports/merge/jobs/", async_merge_reports, name="reports-merge-jobs"),
    path(
        "reports/merge/jobs/<int:scan_job_id>/",
        async_merge_reports,
        name="reports-merge-jobs-detail",
    ),
    path("scans/<int:scan_id>/jobs/", jobs, name="scan-filtered-jobs"),
    path("token/", QuipucordsExpiringAuthTokenView),
    path("status/", status, name="server-status"),
    *ROUTER.urls,
]

v2_urls = [
    *ROUTER_V2.urls,
]

urlpatterns = [
    path("v1/", include((v1_urls, "api"), namespace="v1")),
    path("v2/", include((v2_urls, "api"), namespace="v2")),
]
