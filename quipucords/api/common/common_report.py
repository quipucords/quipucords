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

"""Util for common report operations."""


from quipucords.environment import commit


REPORT_TYPE_DETAILS = 'details'
REPORT_TYPE_DEPLOYMENT = 'deployments'
REPORT_TYPE_CHOICES = ((REPORT_TYPE_DETAILS, REPORT_TYPE_DETAILS),
                       (REPORT_TYPE_DEPLOYMENT, REPORT_TYPE_DEPLOYMENT))


def create_report_version():
    """Create the report version string."""
    return '1.0.0.%s' % commit()
