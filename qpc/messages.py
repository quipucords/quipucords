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

CRED_NAME_HELP = 'Credential name.'
CRED_TYPE_HELP = 'Type of credential. Valid values: vcenter, network.'
CRED_TYPE_FILTER_HELP = 'Filter for listing credentials by type. Valid '\
    'values: vcenter, network.'
CRED_USER_HELP = 'User name for authenticating against the target system.'
CRED_PWD_HELP = 'Password for authenticating against the target system.'
CRED_SSH_HELP = 'File that contains the SSH key.'
CRED_SSH_PSPH_HELP = 'SSH passphrase for authenticating against the target '\
    'system.'
CRED_SUDO_HELP = 'Password for running sudo.'
CRED_CLEAR_ALL_HELP = 'Remove all credentials.'

CRED_ADDED = 'Credential "%s" was added.'

CRED_REMOVED = 'Credential "%s" was removed.'
CRED_FAILED_TO_REMOVE = 'Failed to remove credential "%s". For more '\
    'information, see the server log file.'
CRED_NOT_FOUND = 'Credential "%s" was not found.'
CRED_NO_CREDS_TO_REMOVE = 'No credentials exist to be removed.'
CRED_PARTIAL_REMOVE = 'Some credentials were removed. However, an error '\
    'occurred while removing the following credentials: %s. For more '\
    'information, see the server log file.'
CRED_CLEAR_ALL_SUCCESS = 'All credentials were removed.'

CRED_TYPE_REQUIRED = 'The --type option is required. The value must be set '\
    'to vcenter or network.'
CRED_VC_PWD_AND_USERNAME = 'vCenter Server requires both a user name and '\
    'a password.'
CRED_VC_EDIT_PWD_OR_USERNAME = 'You must update either the user name or the '\
    'password for the vCenter Server credential.'
CRED_VC_KEY_FILE_NOT_ALLOWED = 'vCenter Server cannot use a sudo password, '\
    'SSH keyfile, or SSH passphrase.'
CRED_EDIT_NO_ARGS = 'No arguments were provided to edit credential "%s".'
CRED_DOES_NOT_EXIST = 'Credential "%s" does not exist.'
CRED_UPDATED = 'Credential "%s" was updated.'

CRED_LIST_NO_CREDS = 'No credentials exist yet.'

SOURCE_NAME_HELP = 'Source name.'
SOURCES_NAME_HELP = 'List of source names.'
SOURCE_TYPE_HELP = 'Type of source. Valid values: vcenter, network.'
SOURCE_HOSTS_HELP = 'IP ranges to scan. Run the "man qpc" command for more '\
    'information about supported formats.'
SOURCE_CREDS_HELP = 'Credentials to associate with a source.'
SOURCE_PORT_HELP = 'Port to use for connection for the scan; '\
    'network default is 22, vcenter default is 443.'
SOURCE_SAT_VER_HELP = 'Specify the version of Satellite (for example, "6.2").'
SOURCE_ADD_CREDS_NOT_FOUND = 'An error occurred while processing the '\
    '"--cred" input values. References for the following credential '\
    'could not be found: %s. Failed to add source "%s". '\
    'For more information, see the server log file.'
SOURCE_ADD_CRED_PROCESS_ERR = 'An error occurred while processing the '\
    '"--cred" input values. Failed to add source "%s". For more '\
    'information, see the server log file.'
SOURCE_ADDED = 'Source "%s" was added.'

SOURCE_CLEAR_ALL_HELP = 'Remove all sources.'
SOURCE_REMOVED = 'Source "%s" was removed.'
SOURCE_FAILED_TO_REMOVE = 'Failed to remove source "%s".'
SOURCE_NOT_FOUND = 'Source "%s" was not found.'
SOURCE_NO_SOURCES_TO_REMOVE = 'No sources exist to be removed.'
SOURCE_PARTIAL_REMOVE = 'Some sources were removed. However, an error '\
    'occurred while removing the following sources: %s. For more '\
    'information, see the server log file.'
SOURCE_CLEAR_ALL_SUCCESS = 'All sources were removed.'
SOURCE_EDIT_NO_ARGS = 'No arguments were provided to edit source %s.'
SOURCE_DOES_NOT_EXIST = 'Source "%s" does not exist.'

SOURCE_EDIT_CREDS_NOT_FOUND = 'An error occurred while processing the '\
    '"--cred" input values. References for the following credential '\
    'could not be found: %s. Failed to edit source "%s". For more '\
    'information, see the server log file.'
SOURCE_EDIT_CRED_PROCESS_ERR = 'An error occurred while processing the '\
    '"--cred" input values. Failed to edit source "%s". For more '\
    'information, see the server log file.'
SOURCE_UPDATED = 'Source "%s" was updated.'
SOURCE_LIST_NO_SOURCES = 'No sources exist yet.'
SOURCE_TYPE_FILTER_HELP = 'Filter for listing sources by type. Valid '\
    'values: vcenter, network.'


SCAN_ID_HELP = 'Scan identifier.'
SCAN_TYPE_FILTER_HELP = 'Filter for listing scan jobs by type. Valid '\
    'values: connect, inspect.'
SCAN_STATUS_FILTER_HELP = 'Filter for listing scan jobs by status. Valid '\
    'values: created, pending, running, paused, canceled, completed, failed.'
SCAN_MAX_CONCURRENCY_HELP = 'Maximum number of concurrent scans; '\
    'default is 50.'
SCAN_RESULTS_HELP = 'View results of the specified scan.'
SCAN_DOES_NOT_EXIST = 'Scan "%s" does not exist.'
SCAN_LIST_NO_SCANS = 'No scans found.'
SCAN_STARTED = 'Scan "%s" started.'
SCAN_PAUSED = 'Scan "%s" paused.'
SCAN_RESTARTED = 'Scan "%s" restarted.'
SCAN_CANCELED = 'Scan "%s" canceled.'

VERBOSITY_HELP = 'Verbose mode. Use up to -vvvv for more verbosity.'


CONNECTION_ERROR_MSG = 'A connection error occurred while attempting to '\
                       'communicate with the server. To troubleshoot '\
                       'this problem, check the configuration and the '\
                       'status of the server.'

SSL_ERROR_MSG = 'A connection error occurred while attempting to '\
                'communicate with the server over "https". To troubleshoot '\
                'this problem, check the configuration and the '\
                'status of the server.'

READ_FILE_ERROR = 'Error reading from %s: %s.'
NOT_A_FILE = 'Input %s was not a file.'

VALIDATE_SSHKEY = 'The file path provided, %s, could not be found on the '\
    'system. Provide a valid path for the "--sshkeyfile" argument.'

CONN_PASSWORD = 'Provide a connection password.'
SUDO_PASSWORD = 'Provide a password for sudo.'
SSH_PASSPHRASE = 'Provide a passphrase for the SSH keyfile.'
BECOME_PASSWORD = 'Provide a privilege escalation password to be used when'\
    ' running a network scan.'


SERVER_CONFIG_HOST_HELP = 'Host or IP address for the server.'
SERVER_CONFIG_PORT_HELP = 'Port number for the server; the default is 8000.'

LOGIN_USER_HELP = 'The user name to log in to the server.'
LOGIN_USERNAME_PROMPT = 'User name:'
LOGIN_SUCCESS = 'Login successful.'

LOGOUT_SUCCESS = 'Logged out.'
