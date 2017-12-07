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
PLURAL_HOST_CREDENTIALS_MSG = 'Credentials'
HC_PWD_OR_KEYFILE = 'A host credential must have either' \
                    ' a password or an ssh_keyfile.'
HC_NOT_BOTH = 'A host credential must have either' \
              ' a password or an ssh_keyfile, not both.'
HC_KEY_INVALID = 'ssh_keyfile, %s, is not a valid file on the system.'
HC_NO_KEY_W_PASS = 'A host credential must have an ssh_keyfile provided if' \
    ' a ssh_passphrase is provided.'
HC_NAME_ALREADY_EXISTS = 'Host credential with name=%s already exists'
CRED_TYPE_REQUIRED_CREATED = 'cred_type is required for credential creation'
CRED_TYPE_NOT_ALLOWED_UPDATE = 'cred_type is invalid for credential update'

VC_PWD_AND_USERNAME = 'VCenter requires both username and password.'
VC_KEY_FILE_NOT_ALLOWED = 'VCenter cannot use a sudo password, ssh'\
    ' keyfile, or ssh passphrase.'

# source messages
SOURCE_NAME_ALREADY_EXISTS = 'Source with name=%s already exists'
SOURCE_NAME_VALIDATION = 'Source must have printable name.'
SOURCE_CRED_DISPLAY = 'Credential: %s'
SOURCE_CRED_WRONG_TYPE = 'Credentials must have the same type as source.'
SOURCE_TYPE_REQ = 'A value for source_type must be provided to ' \
                  'create a source.'
SOURCE_TYPE_INV = 'A source_type must not be provided when updating a source.'

NET_HOST_AS_STRING = 'A host range must be a string.'
NET_MIN_HOST = 'Source of type network must have at least one host.'
NET_NO_ADDR = 'Source of type network should not have an address.'
NET_INVALID_RANGE_FORMAT = '%s is not a valid IP range format.'
NET_INVALID_RANGE_CIDR = '%s is not a valid IP or CIDR pattern'
NET_INVALID_HOST = '%s is invalid host'
NET_NO_CIDR_MATCH = '%s does not match CIDR %s'
NET_CIDR_INVALID = '%s has invalid format.'
NET_CIDR_BIT_MASK = '%(ip_range)s has bit mask length %(prefix_bits)s. ' \
                    '%(prefix_bits)s is not in the valid range [0,32].'
NET_FOUR_OCTETS = '%s does not have exactly 4 octets.'
NET_EMPTY_OCTET = '%s has an empty octet.'
NET_CIDR_RANGE = '%(ip_range)s has invalid octet value of %(octet)s.' \
                 ' %(octet)s is not in the range [0,255]'
NET_INVALID_PORT = 'Source of type network must have ssh port in' \
                   ' range [0, 65535]'
NET_MIN_CREDS = 'Source of type network must have at least one ' \
                'set of credentials.'
NET_HC_DO_NOT_EXIST = 'Host credential with id=%d could not be'\
    ' found in database.'


VC_REQ_ADDR = 'Source of type vcenter must have an address.'
VC_NO_HOSTS = 'Source of type vcenter should not have any hosts.'
VC_ONE_CRED = 'Source of type vcenter must a single credential.'

# scan jobs messages
PLURAL_SCAN_JOBS_MSG = 'Scan Jobs'
SJ_REQ_SOURCE = 'Scan must have a source.'

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
