#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Models to capture server information."""

import logging
import uuid

from django.db import models, transaction

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ServerInformation(models.Model):
    """A server's information."""

    global_identifier = models.CharField(max_length=36, null=False)

    def __str__(self):
        """Convert to string."""
        return f"{{id:{self.id}, global_identifier:{self.global_identifier}}}"

    @staticmethod
    @transaction.atomic
    def create_or_retreive_server_id():
        """Create or retreive server's global identifier."""
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
