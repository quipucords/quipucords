"""Defines the models used with the API application.

These models are used in the REST definitions
"""
import ssl
from functools import cached_property

from django.db import models

from api.credential.model import Credential
from constants import DataSources


class Source(models.Model):
    """A source connects a list of credentials and a list of hosts."""

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

    name = models.CharField(max_length=64, unique=True)
    source_type = models.CharField(
        max_length=12, choices=DataSources.choices, null=False
    )
    port = models.IntegerField(null=True)
    ssl_protocol = models.CharField(
        max_length=10, choices=SSL_PROTOCOL_CHOICES, null=True
    )

    ssl_cert_verify = models.BooleanField(null=True)
    disable_ssl = models.BooleanField(null=True)
    use_paramiko = models.BooleanField(null=True)
    credentials = models.ManyToManyField(Credential, related_name="sources")
    hosts = models.JSONField(unique=False, null=False, default=list)
    exclude_hosts = models.JSONField(unique=False, null=True)

    most_recent_connect_scan = models.ForeignKey(
        "api.ScanJob", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    def get_hosts(self):
        """Access hosts as python list instead of str.

        :returns: hosts as a python list
        """
        return self.hosts

    def get_exclude_hosts(self):
        """Access exclude_hosts as a python list.

        :returns: excluded hosts as a python list. Empty list if none exist.
        """
        return self.exclude_hosts or []

    def get_ssl_protocol(self):
        """Obtain the SSL protocol to be used."""
        protocol = None
        if self.ssl_protocol:
            protocol = self.SSL_PROTOCOL_MAPPING.get(self.ssl_protocol)
        return protocol

    def get_ssl_options(self):
        """Returns the ssl_enabled and ssl_verify booleans."""
        ssl_enabled = not self.disable_ssl
        ssl_verify = False
        if ssl_enabled:
            ssl_verify = self.ssl_cert_verify
            if ssl_verify is None:
                ssl_verify = True

        return ssl_enabled, ssl_verify

    @cached_property
    def single_credential(self) -> Credential:
        """Retrieve related credential - for sources that only map to one credential."""
        return self.credentials.get()
