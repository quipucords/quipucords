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
    deployments,
    details,
    insights,
    jobs,
    reports,
    status,
    sync_merge_reports,
)

ROUTER = SimpleRouter()

ROUTER.register(r"credentials", CredentialViewSet, basename="cred")
ROUTER.register(r"reports", DetailsReportsViewSet, basename="reports")
ROUTER.register(r"sources", SourceViewSet, basename="source")
ROUTER.register(r"scans", ScanViewSet, basename="scan")
ROUTER.register(r"jobs", ScanJobViewSet, basename="scanjob")
ROUTER.register(r"users", UserViewSet, basename="users")

# pylint: disable=invalid-name
urlpatterns = [
    path("reports/<int:pk>/details/", details),
    path("reports/<int:pk>/deployments/", deployments),
    path("reports/<int:pk>/insights/", insights),
    path("reports/<int:pk>/", reports),
    path("reports/merge/", sync_merge_reports),
    path("reports/merge/jobs/", async_merge_reports),
    path("reports/merge/jobs/<int:pk>/", async_merge_reports),
    path("scans/<int:pk>/jobs/", jobs),
]

urlpatterns += [path("token/", QuipucordsExpiringAuthTokenView)]

urlpatterns += [
    path("status/", status, name="server-status"),
]

urlpatterns += ROUTER.urls
