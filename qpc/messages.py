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

"""CLI messages for translation."""

AUTH_NAME_HELP = 'auth credential name'
AUTH_USER_HELP = 'user name for authenticating against target system'
AUTH_PWD_HELP = 'password for authenticating against target system'
AUTH_SSH_HELP = 'file containing SSH key'
AUTH_SSH_PSPH_HELP = 'ssh passphrase for authenticating against target system'
AUTH_SUDO_HELP = 'password for running sudo'
AUTH_CLEAR_ALL_HELP = 'remove all credentials'

AUTH_ADDED = 'Auth "%s" was added'

AUTH_REMOVED = 'Auth "%s" was removed'
AUTH_FAILED_TO_REMOVE = 'Failed to remove auth "%s"'
AUTH_NOT_FOUND = 'Auth "%s" was not found'
AUTH_NO_CREDS_TO_REMOVE = 'No credentials exist to be removed'
AUTH_PARTIAL_REMOVE = 'Some credentials were removed, however an error' \
    ' occurred removing the following credentials: %s'
AUTH_CLEAR_ALL_SUCCESS = 'All credentials were removed'

AUTH_EDIT_NO_ARGS = 'No arguments provided to edit credential "%s"'
AUTH_DOES_NOT_EXIST = 'Auth "%s" does not exist'
AUTH_UPDATED = 'Auth "%s" was updated'

AUTH_LIST_NO_CREDS = 'No credentials exist yet.'

PROFILE_NAME_HELP = 'profile name'
PROFILE_HOSTS_HELP = 'IP range to scan. See "man qpc" for supported formats.'
PROFILE_AUTHS_HELP = 'credentials to associate with profile'
PROFILE_SSH_PORT_HELP = 'SSH port for connection; default=22'
PROFILE_ADD_AUTHS_NOT_FOUND = 'An error occurred while processing the ' \
    '"--auth" input values. References for the following auth could not' \
    ' be found: %s. Failed to add profile "%s".'
PROFILE_ADD_AUTH_PROCESS_ERR = 'An error occurred while processing the' \
    ' "--auth" input values. Failed to add profile "%s"'
PROFILE_ADDED = 'Profile "%s" was added'

PROFILE_CLEAR_ALL_HELP = 'remove all network profiles'
PROFILE_REMOVED = 'Profile "%s" was removed'
PROFILE_FAILED_TO_REMOVE = 'Failed to remove profile "%s"'
PROFILE_NOT_FOUND = 'Profile "%s" was not found'
PROFILE_NO_PROFILES_TO_REMOVE = 'No profiles exist to be removed'
PROFILE_PARTIAL_REMOVE = 'Some profiles were removed, however an error' \
    ' occurred removing the following profiles: %s'
PROFILE_CLEAR_ALL_SUCCESS = 'All profiles were removed'
PROFILE_EDIT_NO_ARGS = 'No arguments provided to edit profile %s'
PROFILE_DOES_NOT_EXIST = 'Profile "%s" does not exist'

PROFILE_EDIT_AUTHS_NOT_FOUND = 'An error occurred while processing the' \
    ' "--auth" input  values. References for the following auth ' \
    'could not be found: %s. Failed to edit profile "%s".'
PROFILE_EDIT_AUTH_PROCESS_ERR = 'An error occurred while processing the ' \
    '"--auth" input values. Failed to edit profile "%s"'
PROFILE_UPDATED = 'Profile "%s" was updated'
PROFILE_LIST_NO_PROFILES = 'No profiles exist yet.'

SCAN_ID_HELP = 'scan identifier'
SCAN_MAX_CONCURRENCY_HELP = 'number of concurrent scans; default=50'
SCAN_DOES_NOT_EXIST = 'Scan "%s" does not exist'
SCAN_LIST_NO_SCANS = 'No scans exist yet.'
SCAN_STARTED = 'Scan "%s" started'
SCAN_PAUSED = 'Scan "%s" paused'

VERBOSITY_HELP = 'Verbose mode. Use up to -vvvv for more verbosity.'


CONNECTION_ERROR_MSG = 'A connection error has occurred attempting to' \
                       ' communicate with the server. Check the ' \
                       'configuration and/or the status of the server.'

SSL_ERROR_MSG = 'A connection error has occurred attempting to' \
                ' communicate with the server over "https". Check the' \
                ' configuration and/or the status of the server.'

READ_FILE_ERROR = 'Error reading from %s: %s'
NOT_A_FILE = 'Input %s was not a file.'

VALIDATE_SSHKEY = 'The file path provided, %s, could not be found on the ' \
    'system. Please provide a valid location for the "--sshkeyfile" argument.'

CONN_PASSWORD = 'Provide connection password.'
SUDO_PASSWORD = 'Provide password for sudo.'
SSH_PASSPHRASE = 'Provide passphrase for ssh keyfile.'
