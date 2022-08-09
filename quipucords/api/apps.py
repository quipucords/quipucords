#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Apps module for Django server application."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Defines the api application configuration."""

    name = "api"

    def ready(self):
        """Mark server ready."""
