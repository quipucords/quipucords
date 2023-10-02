"""Models to capture system facts."""

import uuid

from django.db import models

from api.inspectresult.model import RawFactEncoder


class Report(models.Model):
    """A reported set of facts."""

    report_version = models.CharField(max_length=64, null=False)
    # report_platform_id is a unique identifier required by yupana/insights
    report_platform_id = models.UUIDField(default=uuid.uuid4, editable=False)
    # ---------------------------- legacy fields ----------------------------
    # legacy data that should be (re)moved when we transition to the paradigm
    # of "normalization phase"
    sources = models.JSONField(null=False, default=list, encoder=RawFactEncoder)
    deployment_report = models.OneToOneField(
        "DeploymentsReport", models.CASCADE, related_name="report", null=True
    )
    cached_csv = models.TextField(null=True)


default_kwargs = {"unique": False, "blank": True, "null": True}


class Host(models.Model):
    """Representation of a Host."""

    report = models.ForeignKey("Report", on_delete=models.CASCADE, related_name="hosts")
    metadata = models.JSONField(unique=False, null=False, default=dict)
    # canonical facts (https://url.corp.redhat.com/canonical-facts)
    fqdn = models.CharField(max_length=100, **default_kwargs)
    mac_addresses = models.JSONField(unique=False, blank=True, null=True)
    ip_addresses = models.JSONField(unique=False, blank=True, null=True)
    bios_uuid = models.UUIDField(**default_kwargs)
    insights_id = models.CharField(max_length=128, **default_kwargs)
    satellite_id = models.UUIDField(**default_kwargs)
    subscription_manager_id = models.UUIDField(**default_kwargs)
    provider_id = models.CharField(max_length=100, **default_kwargs)
    provider_type = models.CharField(max_length=100, **default_kwargs)
    # system profile facts
    # these facts should follow System Profile (schemas/system_profile/schema.yaml)
    number_of_cpus = models.PositiveIntegerField(**default_kwargs)
    number_of_sockets = models.PositiveIntegerField(**default_kwargs)
    cores_per_socket = models.PositiveIntegerField(**default_kwargs)
    system_memory_bytes = models.PositiveIntegerField(**default_kwargs)
    infrastructure_type = models.CharField(max_length=100, **default_kwargs)
    infrastructure_vendor = models.CharField(max_length=100, **default_kwargs)
    os_release = models.CharField(max_length=100, **default_kwargs)
    arch = models.CharField(max_length=50, **default_kwargs)
    cloud_provider = models.CharField(max_length=50, **default_kwargs)
    system_purpose = models.JSONField(unique=False, null=False, default=dict)
    network_interfaces = models.JSONField(unique=False, null=False, default=list)
    # quipucords facts
    etc_machine_id = models.CharField(max_length=48, **default_kwargs)
    cpu_hyperthreading = models.BooleanField(null=True)
