"""Models to capture server information."""

import logging
import uuid

from django.db import models, transaction

logger = logging.getLogger(__name__)


class ServerInformation(models.Model):
    """A server's information."""

    global_identifier = models.CharField(max_length=36, null=False)

    @staticmethod
    @transaction.atomic
    def create_or_retrieve_server_id():
        """Create or retrieve server's global identifier."""
        server_info = ServerInformation.objects.first()
        if server_info is None:
            server_info = ServerInformation(global_identifier=str(uuid.uuid4()))
            server_info.save()
            logger.info(
                "Server identification not found.  "
                "Initializing server identifier to %s.",
                server_info.global_identifier,
            )
        return server_info.global_identifier
