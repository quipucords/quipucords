"""Constants for quipucords."""

from django.db.models.enums import TextChoices


class DataSources(TextChoices):
    """Django flavored enum for all data sources Quipucords can connect to."""

    NETWORK = "network", "network"
    VCENTER = "vcenter", "vcenter"
    SATELLITE = "satellite", "satellite"
    OPENSHIFT = "openshift", "openshift"
    ANSIBLE = "ansible", "ansible"
    ACS = "acs", "acs"


ENCRYPTED_DATA_MASK = "********"
SCAN_JOB_LOG = "scan-job-{scan_job_id}-{output_type}.txt"
