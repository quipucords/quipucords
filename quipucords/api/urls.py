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

ROUTER.register(r"credentials", CredentialViewSet, basename="cred")
ROUTER.register(r"reports", DetailsReportsViewSet, basename="reports")
ROUTER.register(r"sources", SourceViewSet, basename="source")
ROUTER.register(r"scans", ScanViewSet, basename="scan")
ROUTER.register(r"jobs", ScanJobViewSet, basename="scanjob")
ROUTER.register(r"users", UserViewSet, basename="users")

v1_urls = [
    path("credentials/bulk_delete/", credential_bulk_delete, name="cred-bulk-delete"),
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

urlpatterns = [
    path("v1/", include((v1_urls, "api"), namespace="v1")),
]
