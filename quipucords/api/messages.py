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
NET_INVALID_HOST = "%s is invalid host"
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

# Lightspeed Authorization messages
LIGHTSPEED_INVALID_TOKEN = "Invalid Lightspeed Token received"
LIGHTSPEED_TOKEN_EXPIRED = (
    "Authorization token expired, please log in again to Lightspeed"
)
LIGHTSPEED_TOKEN_EXPIRED_FOR_USER = "Lightspeed Authorization token expired for user %s"
LIGHTSPEED_SSO_CONFIG_QUERY = "Querying Lightspeed SSO configuration at %s for %s"
LIGHTSPEED_SSO_QUERY_FAILED = (
    "Failed to query the Lightspeed SSO configuration: missing %s"
)
LIGHTSPEED_LOGIN_REQUEST = "Requesting Login authorization from %s"
LIGHTSPEED_LOGIN_REQUEST_FAILED = "Failed to request login authorization: %s"
LIGHTSPEED_LOGIN_VERIFYING = "Verifying Login authorization at %s"
LIGHTSPEED_LOGIN_VERIFICATION_FAILED = "Failed to verify Login authorization: %s"
LIGHTSPEED_LOGIN_VERIFICATION_TIMEOUT = "Time-out while waiting for Login authorization"
LIGHTSPEED_RESPONSE = "Response from %s: %s"
LIGHTSPEED_LOGOUT_SUCCESSFUL = "Logged out successfully"
LIGHTSPEED_ALREADY_LOGGED_OUT = "Already logged out"

# HashiCorp Vault messages
HASHICORP_VAULT_NOT_DEFINED = "HashiCorp Vault server is not defined"
HASHICORP_VAULT_ALREADY_EXISTS = "HashiCorp Vault server definition already exists"
HASHICORP_VAULT_MUST_SPECIFY_CA_CERT = "Must specify a ca_cert when ssl_verify is True"
HASHICORP_VAULT_INVALID_ADDRESS = "Address must be a valid FQDN, IPv4 or IPv6 address"
HASHICORP_VAULT_VALID_CLIENT_CERT_REQUIRED = (
    "Valid client certificate is required for HashiCorp Vault authentication"
)
HASHICORP_VAULT_VALID_CLIENT_KEY_REQUIRED = (
    "Valid client key is required for HashiCorp Vault authentication"
)
HASHICORP_VAULT_VALID_CA_CERT_REQUIRED = (
    "Valid CA Cert is required for HashiCorp Vault authentication"
)
HASHICORP_VAULT_FAILED_B64_DECODE_CERT = (
    "Failed to base64 decode the HashiCorp Vault %s, error: %s"
)
HASHICORP_VAULT_FAILED_DECODE_CERT = (
    "Failed to decode the HashiCorp Vault %s, error: %s"
)
HASHICORP_VAULT_AUTHENTICATED = "Authenticated with HashiCorp Vault %s"
HASHICORP_VAULT_FAILED_AUTHENTICATION = "Failed to authenticate to HashiCorp Vault %s"
HASHICORP_VAULT_CONNECTION_ERROR = (
    "Failed to authenticate to HashiCorp Vault %s, ConnectionError: %s"
)
HASHICORP_VAULT_HTTP_ERROR = (
    "Failed to authenticate to HashiCorp Vault %s, BaseHTTPError: %s"
)

# Credential Vault messages
VAULT_SECRET_PATH_REQUIRES_CONFIG = (
    "HashiCorp Vault configuration is required to use vault credentials."
)
VAULT_KEY_REQUIRED = "vault_secret_key is required when using vault_secret_path."
TOKEN_OR_USER_PASS_OR_VAULT = (
    "A credential must have a username+password, auth_token, or vault_secret_path."
)
TOKEN_OR_USER_PASS_OR_VAULT_EXCLUSIVE = (
    "A credential must have only one of username+password, auth_token,"
    " or vault_secret_path."
)
USER_PASS_OR_VAULT = "A credential must have a username+password or vault_secret_path."
USER_PASS_OR_VAULT_NOT_BOTH = (
    "A credential must have either a username+password or vault_secret_path, not both."
)
VAULT_SECRET_AUTH_FAILED = (
    "Failed to authenticate with HashiCorp Vault when reading credential secret."
)
VAULT_SECRET_FETCH_FAILED = (
    "Failed to retrieve secret from HashiCorp Vault (path=%s, mount_point=%s): %s"
)
VAULT_SECRET_NOT_CONFIGURED = (
    "Credential uses vault_secret_path but HashiCorp Vault is not configured."
)
VAULT_SECRET_NO_DATA = "Vault secret at path '%s' (mount_point='%s') returned no data."
VAULT_SECRET_MISSING_KEY = (
    "Vault secret does not contain the expected '%s' key (path='%s')."
)

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

# Publish messages
PUBLISH_NO_AUTH_TOKEN = "No authentication token found. Please log in first."
PUBLISH_TOKEN_EXPIRED = "Authentication token has expired. Please log in again."
PUBLISH_PAYLOAD_FAILED = "Failed to generate report payload: %s"
PUBLISH_CONNECTION_ERROR = "Connection error: %s. Please try again later."
PUBLISH_AUTH_REJECTED = "Authentication rejected by server: %s. Please log in again."
PUBLISH_CLIENT_ERROR = (
    "Request rejected by ingress (%s): %s. This might be a bug in Discovery."
)
PUBLISH_SERVER_ERROR = "Ingress server error (%s): %s. Please try again later."
PUBLISH_UNEXPECTED_RESPONSE = "Unexpected response (%s): %s"

# Publish API messages
PUBLISH_NOT_PUBLISHABLE = "Report cannot be published: %s"
PUBLISH_ALREADY_PENDING = "A publish is already in progress for this report."
