"""API messages for translation."""

# S105 violations here are false positives
# ruff: noqa: S105

# fact messages
FC_REQUIRED_ATTRIBUTE = "Required. May not be null or empty."
FC_SOURCE_NAME_NOT_STR = "Source name must be type string."
FC_MUST_BE_ONE_OF = "Must be one of the following: %s"

# host credential messages
PLURAL_HOST_CREDENTIALS_MSG = "Credentials"
HC_KEYFILE_OR_KEY = (
    "A host credential must have either an ssh_keyfile or an ssh_key, not both."
)
HC_PWD_OR_KEYFILE_OR_KEY = (
    "A host credential must have a password, ssh_keyfile, or ssh_key exclusively."
)
HC_PWD_OR_KEY = "A host credential must have a password or ssh_key exclusively."
HC_PWD_NOT_WITH_KEYFILE = (
    "A host credential must have either a password or an ssh_keyfile, not both."
)
HC_PWD_NOT_WITH_KEY = (
    "A host credential must have either a password or an ssh_key, not both."
)
TOKEN_OR_USER_PASS = (
    "A host credential must have either a username+password or auth_token."
)
TOKEN_OR_USER_PASS_NOT_BOTH = (
    "A host credential must have either a username+password or auth_token, not both."
)
HC_KEY_INVALID = "ssh_keyfile, %s, is not a valid file on the system."
HC_NO_KEY_W_PASS = (
    "A host credential must have an ssh_keyfile or an ssh_key provided if"
    " an ssh_passphrase is provided."
)
HC_NAME_ALREADY_EXISTS = "Host credential with name=%s already exists"
CRED_TYPE_NOT_ALLOWED_UPDATE = "cred_type is invalid for credential update"
CRED_DELETE_NOT_VALID_W_SOURCES = (
    "Credential cannot be deleted because it is used by one or more sources."
)

# source messages
SOURCE_NAME_ALREADY_EXISTS = "Source with name=%s already exists"
SOURCE_NAME_VALIDATION = "Source must have printable name."
SOURCE_HOSTS_CANNOT_BE_EMPTY = "List cannot be empty."
SOURCE_HOST_MUST_BE_JSON_ARRAY = "Must be a JSON array of strings"
SOURCE_CRED_DISPLAY = "Credential: %s"
SOURCE_CRED_WRONG_TYPE = "Credentials must have the same type as source."
SOURCE_TYPE_REQ = "A value for source_type must be provided to create a source."
SOURCE_CONNECTION_SCAN = "The query parameter scan must be a boolean."
SOURCE_TYPE_INV = "A source_type must not be provided when updating a source."
SOURCE_CRED_IDS_INV = "Credential identifiers must be integer values."
SOURCE_MIN_CREDS = "Source must have at least one set of credentials."
SOURCE_DELETE_NOT_VALID_W_SCANS = (
    "Source cannot be deleted because it is used by one or more scans."
)
SOURCE_INVALID_SCHEMA_PROXY_URL = (
    "Enter a valid proxy URL including the protocol, such as 'http://host:port'."
)
SOURCE_INVALID_HOST_PROXY_URL = "Enter a valid proxy URL with a valid host."
SOURCE_INVALID_PORT_PROXY_URL = "Port must be in range [1, 65535]."
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
NET_INVALID_PORT = "Source of type network must have ssh port in range [0, 65535]"
INVALID_PORT = "Port must be an integer."
NET_HC_DO_NOT_EXIST = "Host credential with id=%d could not be found in database."
NET_SSL_OPTIONS_NOT_ALLOWED = "Invalid SSL options for network source: %(options)s"
INVALID_OPTIONS = "Invalid options for '%(source_type)s': %(options)s."
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
SJ_SCAN_DO_NOT_EXIST = "Scan with id=%d could not be found in database."
SJ_SOURCE_DO_NOT_EXIST = "Source with id=%d could not be found in database."
SJ_STATUS_MSG_CREATED = "Job is created."
SJ_STATUS_MSG_RUNNING = "Job is running."
SJ_STATUS_MSG_PENDING = "Job is pending."
SJ_STATUS_MSG_PAUSED = "Job is paused."
SJ_STATUS_MSG_CANCELED = "Job is canceled."
SJ_STATUS_MSG_COMPLETED = "Job is complete."

REPORT_MERGE_REQUIRED = "This field is required"
REPORT_MERGE_NOT_LIST = "This field must be a list of report ids."
REPORT_MERGE_TOO_SHORT = "Two or more scan report ids are required."
REPORT_MERGE_NOT_INT = "Scan report ids must be integers."
REPORT_MERGE_NOT_UNIQUE = "Set of ids must be unique."
REPORT_MERGE_NOT_FOUND = "Not all scan report ids exist. Scan reports not found: %s"

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
PLURAL_SYS_INSPECT_RESULTS_MSG = "System inspection results"
PLURAL_RAW_FACT_MSG = "Raw facts"

QUERY_PARAM_INVALID = "Invalid value for for query parameter %s. Valid inputs are %s."

NO_CANCEL = "Scan cannot be canceled. The scan has already finished or been canceled."

# common serializers
COMMON_CHOICE_STR = "Must be a string. Valid values are %s."
COMMON_CHOICE_BLANK = "This field may not be blank. Valid values are %s."
COMMON_CHOICE_INV = "%s, is an invalid choice. Valid values are %s."
COMMON_ID_INV = "The id must be an integer."

# report messages
REPORTS_TAR_ERROR = "An error occurred compressing files."
REPORT_DEPLOYMENTS_NOT_CREATED = (
    "Deployment report %(report_id)s could not be created. See server logs."
)
REPORT_AGGREGATE_NOT_AVAILABLE = (
    "Aggregate report for Report %(report_id)s is not available."
)
REPORT_INSIGHTS_NOT_CREATED = (
    "Insights report %(report_id)s could not be created. See server logs."
)
REPORT_INSIGHTS_NOT_GENERATED = (
    "Insights report %(report_id)s was not generated because"
    " there were 0 valid hosts. See server logs."
)
REPORT_UNSUPPORTED_REPORT_TYPE = "Unsupported report_type %(report_type)s specified."
