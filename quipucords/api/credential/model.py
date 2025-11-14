"""Defines the models used with the API application.

These models are used in the REST definitions
"""

import tempfile
from contextlib import contextmanager
from itertools import groupby
from pathlib import Path

from django.db import models, transaction
from django.utils.translation import gettext as _

from api import messages
from api.common.models import BaseModel
from api.common.util import ALL_IDS_MAGIC_STRING
from constants import DataSources


class Credential(BaseModel):
    """The credential for connecting to systems."""

    BECOME_USER_DEFAULT = "root"
    BECOME_SUDO = "sudo"
    BECOME_SU = "su"
    BECOME_PBRUN = "pbrun"
    BECOME_PFEXEC = "pfexec"
    BECOME_DOAS = "doas"
    BECOME_DZDO = "dzdo"
    BECOME_KSU = "ksu"
    BECOME_RUNAS = "runas"
    BECOME_METHOD_CHOICES = (
        (BECOME_SUDO, BECOME_SUDO),
        (BECOME_SU, BECOME_SU),
        (BECOME_PBRUN, BECOME_PBRUN),
        (BECOME_PFEXEC, BECOME_PFEXEC),
        (BECOME_DOAS, BECOME_DOAS),
        (BECOME_DZDO, BECOME_DZDO),
        (BECOME_KSU, BECOME_KSU),
        (BECOME_RUNAS, BECOME_RUNAS),
    )

    name = models.CharField(max_length=64, unique=True)
    cred_type = models.CharField(max_length=9, choices=DataSources.choices, null=False)
    # Important note: we allow `null=True` and `blank=True` for most of the fields
    # because this model is overloaded, conditionally expecting values in some fields
    # but not others based on cred_type and other runtime conditions. Input validation
    # exists elsewhere to enforce not-blank values in specific fields when applicable.
    # Future refactoring idea: implement different credential types in separate models.
    username = models.CharField(max_length=64, null=True, blank=True)
    password = models.EncryptedCharField(max_length=1024, null=True, blank=True)
    auth_token = models.EncryptedCharField(max_length=6000, null=True, blank=True)
    ssh_keyfile = models.CharField(max_length=1024, null=True, blank=True)
    ssh_key = models.EncryptedCharField(max_length=65536, null=True, blank=True)
    ssh_passphrase = models.EncryptedCharField(max_length=1024, null=True, blank=True)
    become_method = models.CharField(
        max_length=6, choices=BECOME_METHOD_CHOICES, null=True, blank=True
    )
    become_user = models.CharField(max_length=64, null=True, blank=True)
    become_password = models.EncryptedCharField(max_length=1024, null=True, blank=True)

    class Meta:
        """Metadata for the model."""

        verbose_name_plural = _(messages.PLURAL_HOST_CREDENTIALS_MSG)

    @contextmanager
    def generate_ssh_keyfile(self):
        """Generate a temporary ssh keyfile if credential contains a ssh_key."""
        if self.ssh_key:
            tmp_path = tempfile.NamedTemporaryFile(
                prefix=f"private_key_credential_{self.id}_"
            )
            private_keyfile_path = Path(tmp_path.name)
            private_keyfile_path.write_text(f"{self.ssh_key}\n")
            private_keyfile_path.chmod(0o600)
            yield str(private_keyfile_path)
            # after the context manager is closed, cleanup the file
            tmp_path.close()
        else:
            yield None


def credential_bulk_delete_ids(ids: list | str) -> dict:
    """
    Bulk delete credentials by IDs.

    The `ids` parameter may be either a list of ids or the ALL_IDS_MAGIC_STRING string.

    Returned dict contains lists of IDs for credentials deleted, not found ("missing"),
    and skipped. Example return value:

        {
            "deleted": [1, 2, 3],
            "missing": [],
            "skipped": [
                {"credential": 6, "sources": [1]},
                {"credential": 7, "sources": [2, 3]},
            ],
        }
    """
    with transaction.atomic():
        creds = Credential.objects.all()
        if ids != ALL_IDS_MAGIC_STRING:
            creds = creds.filter(id__in=ids)
        credential_ids_requested = ids if isinstance(ids, set) else set()
        credential_ids_found = set(creds.values_list("id", flat=True))
        credential_ids_with_sources = (
            creds.exclude(sources=None)
            .prefetch_related("sources")
            .values_list("id", "sources")
            .order_by("id")  # later groupby needs sorted input
        )
        creds.filter(sources=None).delete()

    credential_ids_missing = credential_ids_requested - credential_ids_found
    credential_ids_skipped = []

    for credential_id, grouper in groupby(
        credential_ids_with_sources, key=lambda c: c[0]
    ):
        credential_ids_skipped.append(
            {
                "credential": credential_id,
                "sources": [g[1] for g in grouper],
            }
        )
    credential_ids_deleted = credential_ids_found - set(
        c["credential"] for c in credential_ids_skipped
    )

    results = {
        "deleted": credential_ids_deleted,
        "missing": credential_ids_missing,
        "skipped": credential_ids_skipped,
    }
    return results
