"""Utility functions for sources."""

from api.models import Credential

CREDENTIALS_KEY = "credentials"


def expand_credential(json_source):
    """Expand host credentials.

    Take source object with credential id and pull object from db.
    create slim dictionary version of the host credential with name an value
    to return to user.
    """
    cred_ids = json_source.get("credentials", [])
    slim_cred = list(Credential.objects.filter(pk__in=cred_ids).values("id", "name"))
    # Update source JSON with cred JSON
    if slim_cred:
        json_source[CREDENTIALS_KEY] = slim_cred
