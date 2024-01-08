"""Describes the urls and patterns for the API application."""

from django.urls import path
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

urlpatterns = [
    path("credentials/bulk_delete/", credential_bulk_delete),
    path("reports/<int:report_id>/details/", details),
    path("reports/<int:report_id>/deployments/", deployments),
    path("reports/<int:report_id>/insights/", insights),
    path("reports/<int:report_id>/", reports),
    path("reports/merge/jobs/", async_merge_reports),
    path("reports/merge/jobs/<int:scan_job_id>/", async_merge_reports),
    path("scans/<int:scan_id>/jobs/", jobs),
]

urlpatterns += [path("token/", QuipucordsExpiringAuthTokenView)]

urlpatterns += [
    path("status/", status, name="server-status"),
]

urlpatterns += ROUTER.urls
