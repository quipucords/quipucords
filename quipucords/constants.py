"""Constants for quipucords."""

from django.db.models.enums import TextChoices


class DataSources(TextChoices):
    """Django flavored enum for all data sources Quipucords can connect to."""

    NETWORK = "network", "network"
    VCENTER = "vcenter", "vcenter"
    SATELLITE = "satellite", "satellite"
    OPENSHIFT = "openshift", "openshift"


ENCRYPTED_DATA_MASK = "********"
