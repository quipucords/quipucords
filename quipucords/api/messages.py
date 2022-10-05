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

"""API messages for translation."""

# fact messages
FC_REQUIRED_ATTRIBUTE = "Required. May not be null or empty."
FC_SOURCE_NAME_NOT_STR = "Source name must be type string."
FC_MUST_BE_ONE_OF = "Must be one of the following: %s"
FC_MISSING_REPORT_VERSION = (
    "Missing report_version.  "
    "Future releases will not tolerate a missing or invalid report_version."
)

# host credential messages
PLURAL_HOST_CREDENTIALS_MSG = "Credentials"
HOST_USERNAME_CREDENTIAL = "A host credential must have a username."
HC_PWD_OR_KEYFILE = (
    "A host credential must have either" " a password or an ssh_keyfile."
)
HC_NOT_BOTH = (
    "A host credential must have either" " a password or an ssh_keyfile, not both."
)
HC_KEY_INVALID = "ssh_keyfile, %s, is not a valid file on the system."
HC_NO_KEY_W_PASS = (
    "A host credential must have an ssh_keyfile provided if"
    " a ssh_passphrase is provided."
)
HC_NAME_ALREADY_EXISTS = "Host credential with name=%s already exists"
HOST_FIELD_NOT_ALLOWED = "Field not allowed for Host credential."
CRED_TYPE_REQUIRED_CREATED = "cred_type is required for credential creation"
CRED_TYPE_NOT_ALLOWED_UPDATE = "cred_type is invalid for credential update"
CRED_DELETE_NOT_VALID_W_SOURCES = (
    "Credential cannot be deleted " "because it is used by 1 or more sources."
)
VC_PWD_AND_USERNAME = "VCenter requires both username and password."
VC_FIELDS_NOT_ALLOWED = "Field not allowed for Vcenter credential."
SAT_PWD_AND_USERNAME = "Satellite requires both username and password."
SAT_FIELD_NOT_ALLOWED = "Field not allowed for Satellite credential."
UNKNOWN_CRED_TYPE = "Credential type invalid."
OPENSHIFT_CRED_REQUIRED_FIELD = "This field is required for OpenShift credential."
OPENSHIFT_FIELD_NOT_ALLOWED = "Field not allowed for OpenShift credential."

# source messages
SOURCE_NAME_ALREADY_EXISTS = "Source with name=%s already exists"
SOURCE_NAME_VALIDATION = "Source must have printable name."
SOURCE_HOSTS_CANNOT_BE_EMPTY = "List cannot be empty."
SOURCE_HOST_MUST_BE_JSON_ARRAY = "Must be a JSON array of strings"
SOURCE_CRED_DISPLAY = "Credential: %s"
SOURCE_CRED_WRONG_TYPE = "Credentials must have the same type as source."
SOURCE_TYPE_REQ = "A value for source_type must be provided to " "create a source."
SOURCE_CONNECTION_SCAN = "The query parameter scan must be a boolean."
SOURCE_TYPE_INV = "A source_type must not be provided when updating a source."
SOURCE_CRED_IDS_INV = "Credential identifiers must be integer values."
SOURCE_MIN_CREDS = "Source must have at least one set of credentials."
SOURCE_DELETE_NOT_VALID_W_SCANS = (
    "Source cannot be deleted " "because it is used by 1 or more scans."
)

NET_HOST_AS_STRING = "A host range must be a string."
NET_MIN_HOST = "Source of type network must have at least one host."
NET_INVALID_RANGE_FORMAT = "%s is not a valid IP range format."
NET_INVALID_RANGE_CIDR = "%s is not a valid IP or CIDR pattern"
NET_INVALID_HOST = "%s is invalid host"
NET_NO_CIDR_MATCH = "%s does not match CIDR %s"
NET_CIDR_INVALID = "%s has invalid format."
NET_CIDR_BIT_MASK = (
    "%(ip_range)s has bit mask length %(prefix_bits)s. "
    "%(prefix_bits)s is not in the valid range [0,32]."
)
NET_FOUR_OCTETS = "%s does not have exactly 4 octets."
NET_EMPTY_OCTET = "%s has an empty octet."
NET_CIDR_RANGE = (
    "%(ip_range)s has invalid octet value of %(octet)s."
    " %(octet)s is not in the range [0,255]"
)
NET_INVALID_PORT = "Source of type network must have ssh port in" " range [0, 65535]"
NET_HC_DO_NOT_EXIST = "Host credential with id=%d could not be" " found in database."
NET_SSL_OPTIONS_NOT_ALLOWED = "Invalid SSL options for network source: %s"
VC_INVALID_OPTIONS = "Invalid options for vcenter source: %s"
SAT_INVALID_OPTIONS = "Invalid options for satellite source: %s"
SOURCE_ONE_HOST = "This source must have a single host."
SOURCE_EXCLUDE_HOSTS_INCLUDED = "The exclude_hosts option is not valid for this source."
SOURCE_ONE_CRED = "This source must have a single credential."
UNKNOWN_SOURCE_TYPE = "Source type invalid."

# Scan messages
SCAN_NAME_ALREADY_EXISTS = "Scan with name=%s already exists"
SCAN_OPTIONS_EXTENDED_SEARCH_DIR_NOT_LIST = (
    "search_directories must be a JSON array of valid paths"
)
PLURAL_SCANS_MSG = "Scans"

# scan jobs messages
PLURAL_SCAN_JOBS_MSG = "Scan jobs"
SJ_REQ_SOURCES = "Scan job must have one or more sources."
SJ_SCAN_IDS_INV = "Scan identifiers must be integer values."
SJ_SOURCE_IDS_INV = "Source identifiers must be integer values."
SJ_SCAN_DO_NOT_EXIST = "Scan with id=%d could not be" " found in database."
SJ_SOURCE_DO_NOT_EXIST = "Source with id=%d could not be" " found in database."
SJ_STATUS_MSG_CREATED = "Job is created."
SJ_STATUS_MSG_RUNNING = "Job is running."
SJ_STATUS_MSG_PENDING = "Job is pending."
SJ_STATUS_MSG_PAUSED = "Job is paused."
SJ_STATUS_MSG_CANCELED = "Job is canceled."
SJ_STATUS_MSG_COMPLETED = "Job is complete."

SJ_EXTRA_VARS_DICT = "Extra vars must be a dictionary."
SJ_EXTRA_VARS_BOOL = "Extra vars values must be type boolean."
SJ_EXTRA_VARS_KEY = "Extra vars keys must be jboss_eap, jboss_fuse, " "or jboss_brms."

SJ_MERGE_JOB_REQUIRED = "This field is required"
SJ_MERGE_JOB_NOT_LIST = "This field must be a list of job ids."
SJ_MERGE_JOB_TOO_SHORT = "Two or more scan job ids are required."
SJ_MERGE_JOB_NOT_INT = "Scan job ids must be integers."
SJ_MERGE_JOB_NOT_UNIQUE = "Set of ids must be unique."
SJ_MERGE_JOB_NOT_FOUND = "Not all scan job ids exist. Scan jobs not found: %s"
SJ_MERGE_JOB_NOT_COMPLETE = (
    "Not all scan job are completed."
    "  Only completed scan jobs may be merged. Incomplete scan jobs: %s"
)
SJ_MERGE_JOB_NO_RESULTS = (
    "The specified set of jobs" " produced invalid details report.  Error: %s"
)
SJ_MERGE_JOB_NO_TASKS = (
    "Merge cannot be completed. Source for job with " "id=%d has been deleted."
)

REPORT_MERGE_REQUIRED = "This field is required"
REPORT_MERGE_NOT_LIST = "This field must be a list of report ids."
REPORT_MERGE_TOO_SHORT = "Two or more scan report ids are required."
REPORT_MERGE_NOT_INT = "Scan report ids must be integers."
REPORT_MERGE_NOT_UNIQUE = "Set of ids must be unique."
REPORT_MERGE_NOT_FOUND = "Not all scan report ids exist. " "Scan reports not found: %s"
REPORT_MERGE_NO_RESULTS = (
    "The specified set of reports " "produced invalid details report.  Error: %s"
)

# Scan Manager/Signal
SIGNAL_STATE_CHANGE = "SIGNAL %s received for scan job."
SIGNAL_SCAN_MANAGER_CRASH = "Process unexpectedly crashed.  See logs."
SIGNAL_SCAN_MANAGER_RESTART = "Recovering manager."

# scan task messages
PLURAL_SCAN_TASKS_MSG = "Scan tasks"
ST_STATUS_MSG_RUNNING = "Task is running."
ST_STATUS_MSG_RESTARTED = "Task was restarted."
ST_STATUS_MSG_PENDING = "Task is pending."
ST_STATUS_MSG_PAUSED = "Task is paused."
ST_STATUS_MSG_CANCELED = "Task is canceled."
ST_STATUS_MSG_COMPLETED = "Task is complete."
ST_REQ_SOURCE = "Scan task must have a source."

# scan results messages
PLURAL_JOB_CONN_RESULTS_MSG = "Job connection results"
PLURAL_TASK_CONN_RESULTS_MSG = "Task connection results"
PLURAL_SYS_CONN_RESULTS_MSG = "System connection results"
PLURAL_JOB_INSPECT_RESULTS_MSG = "Job inspection results"
PLURAL_TASK_INSPECT_RESULTS_MSG = "Task inspection results"
PLURAL_SYS_INSPECT_RESULTS_MSG = "System inspection results"
PLURAL_RAW_FACT_MSG = "Raw facts"

QUERY_PARAM_INVALID = (
    "Invalid value for for query parameter %s. " "Valid inputs are %s."
)

NO_PAUSE = "Scan cannot be paused. " "The scan must be running for it to be paused."

ALREADY_PAUSED = "Scan cannot be paused. " "The scan is already paused."

NO_CANCEL = (
    "Scan cannot be canceled. " "The scan has already finished or been canceled."
)

NO_RESTART = (
    "Scan cannot be restarted. " "The scan must be paused for it to be restarted."
)

ALREADY_RUNNING = "Scan cannot be restarted. " "The scan is already running."


# common serializers
COMMON_CHOICE_STR = "Must be a string. Valid values are %s."
COMMON_CHOICE_BLANK = "This field may not be blank. Valid values are %s."
COMMON_CHOICE_INV = "%s, is an invalid choice. Valid values are %s."
COMMON_ID_INV = "The id must be an integer."

# report messages
REPORT_GROUP_COUNT_FILTER = (
    "The group_count filter cannot be used with " "other filters."
)
REPORT_GROUP_COUNT_FIELD = (
    "The group_count filter cannot be used with " "the invalid filter key %s."
)
REPORT_INVALID_FILTER_QUERY_PARAM = (
    "One or more filter keys are not " "attributes of the system fingerprint: %s."
)
REPORTS_TAR_ERROR = "An error occured compressing files."
