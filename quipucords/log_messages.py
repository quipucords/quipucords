#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
#
"""Log messages for Quipucords."""

NETWORK_TIMEOUT_ERR = 'A timeout was reached while executing' \
    'the Ansible playbook.'
NETWORK_UNKNOWN_ERR = 'An error occurred while executing the ' \
    'Ansible playbook. See logs for further details.'
NETWORK_CONNECT_CONTINUE = 'Unexpected ansible status %s.  '\
    'Continuing scan because there were %s successful' \
    ' system connections.  Ansible error: %s'
NETWORK_CONNECT_FAIL = 'Unexpected ansible status %s. Failing ' \
    'scan because there were no successful system connections.' \
    ' Ansible error: %s'
