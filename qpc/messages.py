#
# Copyright (c) 2017-2018 Red Hat, Inc.
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

CRED_BECOME_METHOD_HELP = 'The method to become for network privilege '\
    'escalation. Valid values: sudo, su, pbrun, pfexec, doas, dzdo, '\
    'ksu, runas.'
CRED_BECOME_USER_HELP = 'The user to become when running a privileged '\
    'command during network scan.'
CRED_BECOME_PASSWORD_HELP = 'The privilege escalation password to be '\
    'used when running a network scan.'

SOURCE_NAME_HELP = 'Source name.'
SOURCES_NAME_HELP = 'List of source names.'
SOURCE_TYPE_HELP = 'Type of source. Valid values: vcenter, network.'
SOURCE_HOSTS_HELP = 'IP ranges to scan. Run the "man qpc" command for more '\
    'information about supported formats.'
SOURCE_EXCLUDE_HOSTS_HELP = 'IP ranges to exclude from scan. Only supported '\
    'for network sources. Run the "man qpc" command for more information '\
    'about supported formats.'
SOURCE_CREDS_HELP = 'Credentials to associate with a source.'
SOURCE_PORT_HELP = 'Port to use for connection for the scan; '\
    'network default is 22, vcenter default is 443.'
SOURCE_PARAMIKO_HELP = 'Set Ansible connection method to paramiko.'\
    'default connection method is ssh.'
SOURCE_SSL_CERT_HELP = 'If true, the SSL certificate will'\
    ' be verified when making requests to the source, otherwise no '\
    'verification will occur. '\
    'Not valid for network sources.'
SOURCE_SSL_PROTOCOL_HELP = 'The SSL protocol to be used during a secure'\
    ' connection. '\
    'Not valid for network sources.'
SOURCE_SSL_DISABLE_HELP = 'Disable SSL usage during a connection. '\
    'Not valid for network sources.'
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


SCAN_NAME_HELP = 'Scan name.'
SCAN_ADDED = 'Scan "%s" was added.'
SCAN_UPDATED = 'Scan "%s" was updated.'
SCAN_ID_HELP = 'Scan identifier.'
SCAN_JOB_ID_HELP = 'Scan job identifier.'
SCAN_TYPE_FILTER_HELP = 'Filter for listing scan jobs by type. Valid '\
    'values: connect, inspect.'
SCAN_STATUS_FILTER_HELP = 'Filter for listing scan jobs by status. Valid '\
    'values: created, pending, running, paused, canceled, completed, failed.'
SCAN_MAX_CONCURRENCY_HELP = 'Maximum number of concurrent scans; '\
    'default is 50.'
SCAN_RESULTS_HELP = 'View results of the specified scan.'
SCAN_DOES_NOT_EXIST = 'Scan "%s" does not exist.'
SCAN_JOB_DOES_NOT_EXIST = 'Scan job "%s" does not exist.'
SCAN_LIST_NO_SCANS = 'No scans found.'
SCAN_STARTED = 'Scan "%s" started.'
SCAN_PAUSED = 'Scan "%s" paused.'
SCAN_RESTARTED = 'Scan "%s" restarted.'
SCAN_CANCELED = 'Scan "%s" canceled.'
SCAN_CLEAR_ALL_HELP = 'Remove all scans.'
SCAN_REMOVED = 'Scan "%s" was removed.'
SCAN_FAILED_TO_REMOVE = 'Failed to remove scan "%s".'
SCAN_NOT_FOUND = 'Scan "%s" was not found.'
SCAN_NO_SCANS_TO_REMOVE = 'No scans exist to be removed.'
SCAN_PARTIAL_REMOVE = 'Some scans were removed. However, an error '\
    'occurred while removing the following scan: %s. For more '\
    'information, see the server log file.'
SCAN_CLEAR_ALL_SUCCESS = 'All scans were removed.'
SCAN_EDIT_NO_ARGS = 'No arguments were provided to edit scan %s.'
SCAN_JOB_ID_STATUS = 'Provide the "--status" filter with a scan name to '\
    'filter the list of related scan jobs.'
SCAN_EDIT_SOURCES_NOT_FOUND = 'An error occurred while processing the '\
    '"--sources" input values. References for the following sources '\
    'could not be found: %s. Failed to edit scan "%s". For more '\
    'information, see the server log file.'
SCAN_EDIT_SOURCES_PROCESS_ERR = 'An error occurred while processing the '\
    '"--sources" input values. Failed to edit scan "%s". For more '\
    'information, see the server log file.'
SCAN_ENABLED_PRODUCT_HELP = \
    'Contains the list of products to include for extended product search. '\
    'Valid values: jboss_eap, jboss_fuse, jboss_brms, jboss_ws.'
SCAN_EXT_SEARCH_DIRS_HELP = \
    'A list of fully-qualified paths to search for extended product '\
    'search.'

REPORT_DETAIL_DEPRECATED = 'WARNING: "qpc report detail" is deprecated. ' \
    'Use "qpc report details" instead.'
REPORT_SUMMARY_DEPRECATED = 'WARNING: "qpc report summary" is deprecated. ' \
    'Use "qpc report deployments" instead.'

REPORT_JSON_FILE_HELP = 'A list of files that contain the json details ' \
                        'reports to merge.'
REPORT_JSON_DIR_HELP = 'The path to a directory that contain files of json ' \
                       'details reports to merge'
REPORT_JSON_FILES_HELP = 'At least two json details report files are ' \
                         'required to merge.'
REPORT_INVALID_JSON_FILE = 'The file %s does not contain a valid json ' \
                           'details report.'
REPORT_MISSING_REPORT_VERSION = 'WARNING: '\
    'The file %s is missing report_version.  '\
    'Future releases will not tolerate a missing or invalid report_version.'
REPORT_INVALID_REPORT_TYPE = 'The file %s contains invalid report type %s.  '\
    'Only details reports can be merged. Excluding from merge.'
REPORT_JSON_DIR_NO_FILES = \
    'No files with extension .json found in %s.'
REPORT_VALIDATE_JSON = 'Checking files for valid json details report. %s'
REPORT_JSON_DIR_FILE_FAILED = 'Failed: %s is not a details report. '\
    'Excluding from merge.'
REPORT_JSON_MISSING_ATTR = 'Failed: %s is not a details report.'\
    ' Missing %s. Excluding from merge.'
REPORT_JSON_DIR_FILE_SUCCESS = 'Success: %s is a valid details report.'
REPORT_JSON_DIR_ALL_FAIL = 'No details reports were found.'
REPORTS_REPORTS_DO_NOT_EXIST = 'The following scan jobs did not produce ' \
                               'reports: %s.'
REPORT_SCAN_JOB_ID_HELP = 'Scan job identifier.'
REPORT_JOB_ID_HELP = 'Merge report job identifier'
REPORT_REPORT_ID_HELP = 'Report identifier.'
REPORT_REPORT_IDS_HELP = 'Report identifiers.'
REPORT_SCAN_JOB_IDS_HELP = 'Scan job identifiers.'
REPORT_OUTPUT_JSON_HELP = 'Output as a JSON file.'
REPORT_OUTPUT_CSV_HELP = 'Output as a CSV file.'
REPORT_PATH_HELP = 'Output file location.'
REPORT_SJ_DOES_NOT_EXIST = \
    'Scan Job %s does not exist.'
REPORT_SJS_DO_NOT_EXIST = 'The following scan jobs do not exist: %s.'
REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ = \
    'No report summary available for scan job %s.'
REPORT_NO_DEPLOYMENTS_REPORT_FOR_REPORT_ID = \
    'No report summary available for report id %s.'
REPORT_NO_DETAIL_REPORT_FOR_SJ = \
    'No report detail available for scan job %s.'
REPORT_NO_DETAIL_REPORT_FOR_REPORT_ID = \
    'No report detail available for report id %s.'
REPORT_OUTPUT_CANNOT_BE_EMPTY = '%s cannot be empty string.'
REPORT_OUTPUT_IS_A_DIRECTORY = '%s %s was a directory.'
REPORT_DIRECTORY_DOES_NOT_EXIST = \
    'The directory %s does not exist.  Cannot write here.'
REPORT_JSON_DIR_NOT_FOUND = '%s is not a directory'
REPORT_SUCCESSFULLY_WRITTEN = 'Report written successfully.'
REPORT_SUCCESSFULLY_MERGED = 'Report merge job %s created. '\
    'To check merge status, run "qpc report merge-status --job %s"'

DISABLE_OPT_PRODUCTS_HELP = 'The product inspection exclusions. '\
    'Contains the list of products to exclude from inspection. '\
    'Valid values: jboss_eap, jboss_fuse, jboss_brms, jboss_ws.'

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
WRITE_FILE_ERROR = 'Error writing to %s: %s.'
NOT_A_FILE = 'Input %s was not a file.'
FILE_NOT_FOUND = 'Input %s was not found.'

VALIDATE_SSHKEY = 'The file path provided, %s, could not be found on the '\
    'system. Provide a valid path for the "--sshkeyfile" argument.'

CONN_PASSWORD = 'Provide a connection password.'
SUDO_PASSWORD = 'Provide a password for sudo.'
SSH_PASSPHRASE = 'Provide a passphrase for the SSH keyfile.'
BECOME_PASSWORD = 'Provide a privilege escalation password to be used when '\
    'running a network scan.'

MERGE_JOB_ID_NOT_FOUND = 'Report merge job %s not found.'
MERGE_JOB_ID_STATUS = 'Report merge job %s is %s.'
DISPLAY_REPORT_ID = \
    'Created merge report with id: "%s". To download report, run "qpc report' \
    ' summary --report %s --csv --output-file temp.csv"'
SERVER_CONFIG_REQUIRED = 'Configure server using command below:'
SERVER_LOGIN_REQUIRED = 'Log in using the command below:'
SERVER_CONFIG_HOST_HELP = 'Host or IP address for the server.'
SERVER_CONFIG_PORT_HELP = 'Port number for the server; the default is 443.'
SERVER_CONFIG_SSL_CERT_HELP = 'File path to the SSL certificate '\
    'to use for verification.'
SERVER_CONFIG_SUCCESS = 'Server connectivity was successfully configured. '\
    'The server will be contacted via "%s" at host "%s" with port "%s".'
SERVER_INTERNAL_ERROR = 'An internal server error occurred. For more '\
    'information, see the server log file.'
SERVER_STATUS_FAILURE = 'Unexpected failure occurred when accessing the '\
    'status endpoint.'
STATUS_PATH_HELP = 'Output file location.'
STATUS_SUCCESSFULLY_WRITTEN = 'Server status written successfully.'

LOGIN_USER_HELP = 'The user name to log in to the server.'
LOGIN_USERNAME_PROMPT = 'User name: '
LOGIN_SUCCESS = 'Login successful.'

LOGOUT_SUCCESS = 'Logged out.'

NEXT_RESULTS = 'Press enter to see the next set of results.'
