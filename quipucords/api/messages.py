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
#

"""API messages for translation."""

# fact messages
VALIDATE_FACTS_MSG = 'A least one fact is required.'

# host credential messages
PLURAL_HOST_CREDENTIALS_MSG = 'Host Credentials'
HC_PWD_OR_KEYFILE = 'A host credential must have either' \
                    ' a password or an ssh_keyfile.'
HC_NOT_BOTH = 'A host credential must have either' \
              ' a password or an ssh_keyfile, not both.'
HC_KEY_INVALID = 'ssh_keyfile, %s, is not a valid file on the system.'
HC_NO_KEY_W_PASS = 'A host credential must have an ssh_keyfile provided if' \
    ' a ssh_passphrase is provided.'

# network profile messages
NP_HOST_AS_STRING = 'A host range must be a string.'
NP_CRED_DISPLAY = 'Credential: %s'
NP_NAME_VALIDATION = 'Network profile must have printable name.'
NP_MIN_HOST = 'Network profile must have at least one host.'
NP_INVALID_RANGE_FORMAT = '%s is not a valid IP range format.'
NP_INVALID_RANGE_CIDR = '%s is not a valid IP or CIDR pattern'
NP_INVALID_HOST = '%s is invalid host'
NP_NO_CIDR_MATCH = '%s does not match CIDR %s'
NP_CIDR_INVALID = '%s has invalid format.'
NP_CIDR_BIT_MASK = '%(ip_range)s has bit mask length %(prefix_bits)s. ' \
                   '%(prefix_bits)s is not in the valid range [0,32].'
NP_FOUR_OCTETS = '%s does not have exactly 4 octets.'
NP_EMPTY_OCTET = '%s has an empty octet.'
NP_CIDR_RANGE = '%(ip_range)s has invalid octet value of %(octet)s.' \
                ' %(octet)s is not in the range [0,255]'
NP_INVALID_PORT = 'Network profile must have ssh port in range [0, 65535]'
NP_MIN_CREDS = 'Network profile must have at least one set of credentials.'

# scan jobs messages
PLURAL_SCAN_JOBS_MSG = 'Scan Jobs'
SJ_REQ_PROFILE = 'Scan must have a network profile.'

# scan results messages
PLURAL_SCAN_RESULTS_MSG = 'Scan Results'
PLURAL_KEY_VALUES_MSG = 'Result Key Values'
PLURAL_RESULTS_MSG = 'Results'

NO_PAUSE = 'Scan cannot be paused. ' \
    'The scan must be running for it to be paused.'

ALREADY_PAUSED = 'Scan cannot be paused. ' \
    'The scan is already paused.'

NO_CANCEL = 'Scan cannot be canceled. ' \
    'The scan has already finished or been canceled.'

NO_RESTART = 'Scan cannot be restarted. ' \
    'The scan must be paused for it to be restarted.'

ALREADY_RUNNING = 'Scan cannot be restarted. ' \
    'The scan is already running.'
