"""Admin module for Django server application."""

from django.contrib import admin

from api.models import (
    Credential,
    DetailsReport,
    JobConnectionResult,
    JobInspectionResult,
    Scan,
    ScanJob,
    ServerInformation,
    Source,
    SystemFingerprint,
)

admin.site.register(ServerInformation)
admin.site.register(DetailsReport)
admin.site.register(Credential)
admin.site.register(Source)
admin.site.register(SystemFingerprint)
admin.site.register(Scan)
admin.site.register(ScanJob)
admin.site.register(JobConnectionResult)
admin.site.register(JobInspectionResult)
