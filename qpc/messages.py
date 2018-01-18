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

CRED_NAME_HELP = 'credential credential name'
CRED_TYPE_HELP = 'type of credential.  Valid values: vcenter, network'
CRED_TYPE_FILTER_HELP = 'type filter for listing credentials.  Valid '\
    'values: vcenter, network'
CRED_USER_HELP = 'user name for authenticating against target system'
CRED_PWD_HELP = 'password for authenticating against target system'
CRED_SSH_HELP = 'file containing SSH key'
CRED_SSH_PSPH_HELP = 'ssh passphrase for authenticating against target system'
CRED_CLEAR_ALL_HELP = 'remove all credentials'

CRED_ADDED = 'Credential "%s" was added'

CRED_REMOVED = 'Credential "%s" was removed'
CRED_FAILED_TO_REMOVE = 'Failed to remove credential "%s"'
CRED_NOT_FOUND = 'Credential "%s" was not found'
CRED_NO_CREDS_TO_REMOVE = 'No credentials exist to be removed'
CRED_PARTIAL_REMOVE = 'Some credentials were removed, however an error' \
    ' occurred removing the following credentials: %s'
CRED_CLEAR_ALL_SUCCESS = 'All credentials were removed'

CRED_TYPE_REQUIRED = '--type is required; Must be set to vcenter or network'
CRED_VC_PWD_AND_USERNAME = 'VCenter requires both username and password.'
CRED_VC_EDIT_PWD_OR_USERNAME = 'Must update either username or password '
'for VCenter credentials'
CRED_VC_FIELDS_NOT_ALLOWED = 'VCenter cannot use a become password, ssh'\
    ' keyfile, become user, become method, or ssh passphrase.'
CRED_EDIT_NO_ARGS = 'No arguments provided to edit credential "%s"'
CRED_DOES_NOT_EXIST = 'Credential "%s" does not exist'
CRED_UPDATED = 'Credential "%s" was updated'

CRED_LIST_NO_CREDS = 'No credentials exist yet.'

CRED_BECOME_METHOD_HELP = 'Method to become for network privilege escalation.'\
    ' Valid values: sudo, su, pbrun, pfexec, doas, dzdo, ksu, runas.'
CRED_BECOME_USER_HELP = 'The user to become when running a privileged command'\
    ' during network scan.'
CRED_BECOME_PASSWORD_HELP = 'The privilege escalation password to be used' \
    ' when running a network scan.'

SOURCE_NAME_HELP = 'source name'
SOURCES_NAME_HELP = 'list of source names'
SOURCE_TYPE_HELP = 'type of source.  Valid values: vcenter, network'
SOURCE_HOSTS_HELP = 'IP ranges to scan. See "man qpc" for supported formats.'
SOURCE_CREDS_HELP = 'credentials to associate with source'
SOURCE_PORT_HELP = 'port for connection; network default=22, '\
    'vcenter default=443'
SOURCE_SAT_VER_HELP = 'specify the version of Satellite (i.e. "6.2")'
SOURCE_ADD_CREDS_NOT_FOUND = 'An error occurred while processing the ' \
    '"--cred" input values. References for the'\
    ' following credential could not' \
    ' be found: %s. Failed to add source "%s".'
SOURCE_ADD_CRED_PROCESS_ERR = 'An error occurred while processing the' \
    ' "--cred" input values. Failed to add source "%s"'
SOURCE_ADDED = 'Source "%s" was added'

SERVER_CONFIG_HOST_HELP = 'host or ip address'
SERVER_CONFIG_PORT_HELP = 'port number; default=8000'

SOURCE_CLEAR_ALL_HELP = 'remove all sources'
SOURCE_REMOVED = 'Source "%s" was removed'
SOURCE_FAILED_TO_REMOVE = 'Failed to remove source "%s"'
SOURCE_NOT_FOUND = 'Source "%s" was not found'
SOURCE_NO_SOURCES_TO_REMOVE = 'No sources exist to be removed'
SOURCE_PARTIAL_REMOVE = 'Some sources were removed, however an error' \
    ' occurred removing the following sources: %s'
SOURCE_CLEAR_ALL_SUCCESS = 'All sources were removed'
SOURCE_EDIT_NO_ARGS = 'No arguments provided to edit source %s'
SOURCE_DOES_NOT_EXIST = 'Source "%s" does not exist'

SOURCE_EDIT_CREDS_NOT_FOUND = 'An error occurred while processing the' \
    ' "--cred" input  values. References for the following credential ' \
    'could not be found: %s. Failed to edit source "%s".'
SOURCE_EDIT_CRED_PROCESS_ERR = 'An error occurred while processing the ' \
    '"--cred" input values. Failed to edit source "%s"'
SOURCE_UPDATED = 'Source "%s" was updated'
SOURCE_LIST_NO_SOURCES = 'No sources exist yet.'
SOURCE_TYPE_FILTER_HELP = 'type filter for listing sources.  Valid '\
    'values: vcenter, network'


SCAN_ID_HELP = 'scan identifier'
SCAN_TYPE_FILTER_HELP = 'type filter for listing scan jobs.  Valid '\
    'values: connect, inspect'
SCAN_STATUS_FILTER_HELP = 'status filter for listing scan jobs.  Valid '\
    'values: created, pending, running, paused, canceled, completed, failed'
SCAN_MAX_CONCURRENCY_HELP = 'number of concurrent scans; default=50'
SCAN_RESULTS_HELP = 'view results of specified scan'
SCAN_DOES_NOT_EXIST = 'Scan "%s" does not exist'
SCAN_LIST_NO_SCANS = 'No scans found.'
SCAN_STARTED = 'Scan "%s" started'
SCAN_PAUSED = 'Scan "%s" paused'
SCAN_RESTARTED = 'Scan "%s" restarted'
SCAN_CANCELED = 'Scan "%s" canceled'

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
SSH_PASSPHRASE = 'Provide passphrase for ssh keyfile.'
BECOME_PASSWORD = 'Provide privilege escalation password to be used when'\
    ' running a network scan.'

LOGIN_USER_HELP = 'The username to login to the server.'
LOGIN_USERNAME_PROMPT = 'Username:'
LOGIN_SUCCESS = 'Login successful.'

LOGOUT_SUCCESS = 'Logged out.'
