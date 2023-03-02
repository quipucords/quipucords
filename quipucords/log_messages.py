"""Log messages for Quipucords."""

NETWORK_TIMEOUT_ERR = "A timeout was reached while executing the Ansible playbook."
NETWORK_UNKNOWN_ERR = (
    "An error occurred while executing the "
    "Ansible playbook. See logs for further details."
)
NETWORK_CONNECT_CONTINUE = (
    "Unexpected ansible status %s.  "
    "Continuing scan because there were %s successful"
    " system connections.  Ansible error: %s"
)
NETWORK_CONNECT_FAIL = (
    "Unexpected ansible status %s. Failing "
    "scan because there were no successful system connections."
    " Ansible error: %s"
)
NETWORK_CALLBACK_ACK_STOP = (
    "NETWORK %s CALLBACK: Acknowledged request to %s but still processing."
)
NETWORK_PLAYBOOK_STOPPED = "NETWORK %s: Playbook status has been reported as %s."
TASK_UNEXPECTED_FAILURE = "UNEXPECTED FAILURE in %s.  Error: %s\nAnsible result: %s"
TASK_PERMISSION_DENIED = "PERMISSION DENIED %s could not connect with cred %s."
