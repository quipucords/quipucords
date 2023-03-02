"""Defines the models used with the API application.

These models are used in the REST definitions
"""
import json
import ssl
from functools import cached_property

from django.db import models

from api.credential.model import Credential


class SourceOptions(models.Model):
    """The source options allows configuration of a sources."""

    SSL_PROTOCOL_SSLv23 = "SSLv23"
    SSL_PROTOCOL_TLSv1 = "TLSv1"
    SSL_PROTOCOL_TLSv1_1 = "TLSv1_1"
    SSL_PROTOCOL_TLSv1_2 = "TLSv1_2"
    SSL_PROTOCOL_CHOICES = (
        (SSL_PROTOCOL_SSLv23, SSL_PROTOCOL_SSLv23),
        (SSL_PROTOCOL_TLSv1, SSL_PROTOCOL_TLSv1),
        (SSL_PROTOCOL_TLSv1_1, SSL_PROTOCOL_TLSv1_1),
        (SSL_PROTOCOL_TLSv1_2, SSL_PROTOCOL_TLSv1_2),
    )

    SSL_PROTOCOL_MAPPING = {
        SSL_PROTOCOL_SSLv23: ssl.PROTOCOL_SSLv23,
        SSL_PROTOCOL_TLSv1: ssl.PROTOCOL_TLSv1,
        SSL_PROTOCOL_TLSv1_1: ssl.PROTOCOL_TLSv1_1,
        SSL_PROTOCOL_TLSv1_2: ssl.PROTOCOL_TLSv1_2,
    }

    ssl_protocol = models.CharField(
        max_length=10, choices=SSL_PROTOCOL_CHOICES, null=True
    )

    ssl_cert_verify = models.BooleanField(null=True)
    disable_ssl = models.BooleanField(null=True)
    use_paramiko = models.BooleanField(null=True)

    def get_ssl_protocol(self):
        """Obtain the SSL protocol to be used."""
        protocol = None
        if self.ssl_protocol:
            protocol = self.SSL_PROTOCOL_MAPPING.get(self.ssl_protocol)
        return protocol


class Source(models.Model):
    """A source connects a list of credentials and a list of hosts."""

    NETWORK_SOURCE_TYPE = "network"
    VCENTER_SOURCE_TYPE = "vcenter"
    SATELLITE_SOURCE_TYPE = "satellite"
    OPENSHIFT_SOURCE_TYPE = "openshift"
    SOURCE_TYPE_CHOICES = (
        (NETWORK_SOURCE_TYPE, NETWORK_SOURCE_TYPE),
        (VCENTER_SOURCE_TYPE, VCENTER_SOURCE_TYPE),
        (SATELLITE_SOURCE_TYPE, SATELLITE_SOURCE_TYPE),
        (OPENSHIFT_SOURCE_TYPE, OPENSHIFT_SOURCE_TYPE),
    )

    name = models.CharField(max_length=64, unique=True)
    source_type = models.CharField(
        max_length=12, choices=SOURCE_TYPE_CHOICES, null=False
    )
    port = models.IntegerField(null=True)
    options = models.OneToOneField(SourceOptions, null=True, on_delete=models.CASCADE)
    credentials = models.ManyToManyField(Credential)
    hosts = models.TextField(unique=False, null=False)
    exclude_hosts = models.TextField(unique=False, null=True)

    most_recent_connect_scan = models.ForeignKey(
        "api.ScanJob", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    def get_hosts(self):
        """Access hosts as python list instead of str.

        :returns: hosts as a python list
        """
        return json.loads(self.hosts)

    def get_exclude_hosts(self):
        """Access exclude_hosts as python list instead of str.

        :returns: excluded hosts as a python list. Empty list if none exist.
        """
        if self.exclude_hosts:
            return json.loads(self.exclude_hosts)
        return []

    @cached_property
    def single_credential(self) -> Credential:
        """Retrieve related credential - for sources that only map to one credential."""
        return self.credentials.get()
