#
# Copyright (c) 2017-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTask used for network connection discovery."""
import logging
import os.path

import ansible_runner
import pexpect
from ansible_runner.exceptions import AnsibleRunnerException
from django.db import transaction

import log_messages
from api.models import (
    Credential,
    ScanJob,
    ScanOptions,
    ScanTask,
    SystemConnectionResult,
)
from api.serializers import CredentialSerializer, SourceSerializer
from api.vault import decrypt_data_as_unicode, write_to_yaml
from quipucords import settings
from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.utils import (
    _construct_vars,
    check_manager_interrupt,
    expand_hostpattern,
)
from scanner.task import ScanTaskRunner

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


# The ConnectTaskRunner creates a new ConnectResultCallback for each
# credential it tries to connect with, and the ConnectResultCallbacks
# all forward their information to a single ConnectResultStore.
class ConnectResultStore:
    """This object knows how to record and retrieve connection results."""

    def __init__(self, scan_task):
        """Initialize ConnectResultStore object."""
        self.scan_task = scan_task

        source = scan_task.source

        # Sources can contain patterns that describe multiple hosts,
        # like '1.2.3.[4:6]'. Expand the patterns so hosts is a list
        # of single hosts we can try to connect to.

        hosts, exclude_hosts = [], []

        hosts_list = source.get_hosts()
        exclude_hosts_list = source.get_exclude_hosts()

        for host in hosts_list:
            hosts.extend(expand_hostpattern(host))
        for host in exclude_hosts_list:
            exclude_hosts.extend(expand_hostpattern(host))

        # Remove excluded ip addresses from the hosts list.
        hosts = list(set(hosts) - set(exclude_hosts))

        self._remaining_hosts = set(hosts)

        scan_task.update_stats(
            "INITIAL NETWORK CONNECT STATS.",
            sys_count=len(hosts),
            sys_scanned=0,
            sys_failed=0,
            sys_unreachable=0,
        )

    @transaction.atomic
    def record_result(self, name, source, credential, status):
        """Record a new result, either a connection success or a failure."""
        sys_result = SystemConnectionResult(
            name=name,
            source=source,
            credential=credential,
            status=status,
            task_connection_result=self.scan_task.connection_result,
        )
        sys_result.save()

        if status == SystemConnectionResult.SUCCESS:
            message = "%s with %s" % (name, credential.name)
            self.scan_task.increment_stats(
                message, increment_sys_scanned=True, prefix="CONNECTED"
            )
        elif status == SystemConnectionResult.UNREACHABLE:
            message = "%s is UNREACHABLE" % (name)
            self.scan_task.increment_stats(
                message, increment_sys_unreachable=True, prefix="FAILED"
            )
        else:
            if credential is not None:
                message = "%s with %s" % (name, credential.name)
            else:
                message = "%s has no valid credentials" % name

            self.scan_task.increment_stats(
                message, increment_sys_failed=True, prefix="FAILED"
            )

        self._remaining_hosts.remove(name)

    def remaining_hosts(self):
        """Get the set of hosts that are left to scan."""
        # Need to return a list becuase the caller can iterate over
        # our return value and call record_result repeatedly. If we
        # returned the actual list, then they would get a 'set changed
        # size during iteration' error.
        return list(self._remaining_hosts)


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def execute_task(self, manager_interrupt):
        """Scan network range and attempt connections."""
        result_store = ConnectResultStore(self.scan_task)
        scan_message, scan_result = self.run_with_result_store(
            manager_interrupt, result_store
        )
        return scan_message, scan_result

    # pylint: disable=too-many-locals
    def run_with_result_store(self, manager_interrupt, result_store):
        """Run with a given ConnectResultStore."""
        serializer = SourceSerializer(self.scan_task.source)
        source = serializer.data

        if self.scan_job.options is not None:
            forks = self.scan_job.options.max_concurrency
        else:
            forks = ScanOptions.get_default_forks()

        if self.scan_task.source.options is not None:
            use_paramiko = self.scan_task.source.options.use_paramiko
        else:
            use_paramiko = False

        connection_port = source["port"]
        credentials = source["credentials"]

        remaining_hosts = result_store.remaining_hosts()

        for cred_id in credentials:
            check_manager_interrupt(manager_interrupt.value)
            credential = Credential.objects.get(pk=cred_id)
            if not remaining_hosts:
                message = (
                    "Skipping credential %s.  No remaining hosts." % credential.name
                )
                self.scan_task.log_message(message)
                break

            message = "Attempting credential %s." % credential.name
            self.scan_task.log_message(message)

            try:
                scan_message, scan_result = _connect(
                    manager_interrupt,
                    self.scan_task,
                    remaining_hosts,
                    result_store,
                    credential,
                    connection_port,
                    forks,
                    use_paramiko,
                )
                if scan_result != ScanTask.COMPLETED:
                    return scan_message, scan_result
            except AnsibleRunnerException as ansible_error:
                remaining_hosts_str = ", ".join(result_store.remaining_hosts())
                error_message = (
                    "Connect scan task failed with credential %s."
                    " Error: %s Hosts: %s"
                    % (credential.name, ansible_error, remaining_hosts_str)
                )
                return error_message, ScanTask.FAILED

            remaining_hosts = result_store.remaining_hosts()

            logger.debug("Failed systems: %s", remaining_hosts)

        for host in remaining_hosts:
            # We haven't connected to these hosts with any
            # credentials, so they have failed.
            result_store.record_result(
                host, self.scan_task.source, None, SystemConnectionResult.FAILED
            )

        return None, ScanTask.COMPLETED


# pylint: disable=too-many-arguments, too-many-locals,
# pylint: disable=too-many-statements, too-many-branches
def _connect(
    manager_interrupt,
    scan_task,
    hosts,
    result_store,
    credential,
    connection_port,
    forks,
    use_paramiko=False,
    exclude_hosts=None,
    base_ssh_executable=None,
    ssh_timeout=None,
):
    """Attempt to connect to hosts using the given credential.

    :param manager_interrupt: Signal used to communicate termination of scan
    :param scan_task: The scan task for this connection job
    :param hosts: The collection of hosts to test connections
    :param result_store: The result store to accept the results.
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :param use_paramiko: use paramiko instead of ssh for connection
    :param forks: number of forks to run with
    :param exclude_hosts: Optional. Hosts to exclude from test connections
    :param base_ssh_executable: ssh executable, or None for
            'ssh'. Will be wrapped with a timeout before being passed
            to Ansible.
        :param ssh_timeout: string in the format of the 'timeout'
            command. Timeout for individual tasks.
    :returns: list of connected hosts credential tuples and
            list of host that failed connection
    """
    cred_data = CredentialSerializer(credential).data

    ssh_executable = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../bin/timeout_ssh")
    )

    base_ssh_executable = base_ssh_executable or "ssh"
    ssh_timeout = ssh_timeout or settings.QPC_SSH_CONNECT_TIMEOUT

    # pylint: disable=line-too-long
    # the ssh arg is required for become-pass because
    # ansible checks for an exact string match of ssh
    # anywhere in the command array
    # See https://github.com/ansible/ansible/blob/stable-2.3/lib/ansible/plugins/connection/ssh.py#L490-L500 # noqa
    # timeout_ssh will remove the ssh argument before running the command
    ssh_args = [
        "--executable=" + base_ssh_executable,
        "--timeout=" + ssh_timeout,
        "ssh",
    ]
    group_names, inventory = _construct_connect_inventory(
        hosts,
        cred_data,
        connection_port,
        forks,
        exclude_hosts,
        ssh_executable,
        ssh_args,
    )
    inventory_file = write_to_yaml(inventory)
    _handle_ssh_passphrase(cred_data)

    log_message = (
        "START CONNECT PROCESSING GROUPS"
        " with use_paramiko: %s and %d forks" % (use_paramiko, forks)
    )
    scan_task.log_message(log_message)
    for idx, group_name in enumerate(group_names):
        check_manager_interrupt(manager_interrupt.value)
        group_ips = (
            inventory.get("all").get("children").get(group_name).get("hosts").keys()
        )
        group_ips = ["'%s'" % ip for ip in group_ips]
        group_ip_string = ", ".join(group_ips)
        log_message = (
            "START CONNECT PROCESSING GROUP %d of %d. "
            "About to connect to hosts [%s]"
            % ((idx + 1), len(group_names), group_ip_string)
        )
        scan_task.log_message(log_message)
        call = ConnectResultCallback(
            result_store, credential, scan_task.source, manager_interrupt
        )

        # Create parameters for ansible runner
        runner_settings = {"job_timeout": int(settings.NETWORK_CONNECT_JOB_TIMEOUT)}
        extra_vars_dict = {"variable_host": group_name}
        playbook_path = os.path.join(
            settings.BASE_DIR, "scanner/network/runner/connect.yml"
        )
        cmdline_list = []
        vault_file_path = "--vault-password-file=%s" % (settings.DJANGO_SECRET_PATH)
        cmdline_list.append(vault_file_path)
        forks_cmd = "--forks=%s" % (forks)
        cmdline_list.append(forks_cmd)
        if use_paramiko:
            cmdline_list.append("--connection=paramiko")  # paramiko conn
        all_commands = " ".join(cmdline_list)
        if int(settings.ANSIBLE_LOG_LEVEL) == 0:
            quiet_bool = True
            verbosity_lvl = 0
        else:
            quiet_bool = False
            verbosity_lvl = int(settings.ANSIBLE_LOG_LEVEL)
        try:
            runner_obj = ansible_runner.run(
                quiet=quiet_bool,
                settings=runner_settings,
                inventory=inventory_file,
                extravars=extra_vars_dict,
                event_handler=call.event_callback,
                cancel_callback=call.cancel_callback,
                playbook=playbook_path,
                cmdline=all_commands,
                verbosity=verbosity_lvl,
            )
        except Exception as err_msg:
            raise AnsibleRunnerException(err_msg)

        final_status = runner_obj.status
        if final_status != "successful":
            if final_status == "canceled":
                if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
                    msg = log_messages.NETWORK_PLAYBOOK_STOPPED % (
                        "CONNECT",
                        "canceled",
                    )
                    return msg, scan_task.CANCELED
                msg = log_messages.NETWORK_PLAYBOOK_STOPPED % ("CONNECT", "paused")
                return msg, scan_task.PAUSED
            if final_status not in ["unreachable", "failed", "canceled"]:
                if final_status == "timeout":
                    error = log_messages.NETWORK_TIMEOUT_ERR
                else:
                    error = log_messages.NETWORK_UNKNOWN_ERR
                if scan_task.systems_scanned:
                    msg = log_messages.NETWORK_CONNECT_CONTINUE % (
                        final_status,
                        str(scan_task.systems_scanned),
                        error,
                    )
                    scan_task.log_message(msg, log_level=logging.ERROR)
                else:
                    msg = log_messages.NETWORK_CONNECT_FAIL % (final_status, error)
                    return msg, scan_task.FAILED
    return None, scan_task.COMPLETED


def _handle_ssh_passphrase(credential):
    """Attempt to setup login via passphrase if necessary.

    :param credential: The credential used for connections
    """
    if (
        credential.get("ssh_keyfile") is not None
        and credential.get("ssh_passphrase") is not None
    ):
        keyfile = credential.get("ssh_keyfile")
        passphrase = decrypt_data_as_unicode(credential["ssh_passphrase"])
        cmd_string = "ssh-add {}".format(keyfile)

        try:
            child = pexpect.spawn(cmd_string, timeout=12)
            phrase = [pexpect.EOF, "Enter passphrase for .*:"]
            i = child.expect(phrase)
            while i:
                child.sendline(passphrase)
                i = child.expect(phrase)
        except pexpect.exceptions.TIMEOUT:
            pass


def _construct_connect_inventory(
    hosts,
    credential,
    connection_port,
    concurrency_count,
    exclude_hosts=None,
    ssh_executable=None,
    ssh_args=None,
):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts to test connections
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :param concurrency_count: The number of concurrent scans
    :param exclude_hosts: Optional. Hosts to exclude test connections
    :param ssh_executable: the ssh executable to use, or None for 'ssh'
    :param ssh_args: a list of extra ssh arguments, or None
    :returns: A dictionary of the ansible inventory
    """
    if exclude_hosts is not None:
        hosts = list(set(hosts) - set(exclude_hosts))

    concurreny_groups = list(
        [
            hosts[i : i + concurrency_count]
            for i in range(0, len(hosts), concurrency_count)
        ]
    )

    vars_dict = _construct_vars(connection_port, credential)
    children = {}
    inventory = {"all": {"children": children, "vars": vars_dict}}
    i = 0
    group_names = []
    for concurreny_group in concurreny_groups:
        hosts_dict = {}
        for host in concurreny_group:
            host_vars = {}
            host_vars["ansible_host"] = host
            if ssh_executable:
                host_vars["ansible_ssh_executable"] = ssh_executable
            if ssh_args:
                host_vars["ansible_ssh_common_args"] = " ".join(ssh_args)
            hosts_dict[host] = host_vars

        group_name = "group_{}".format(i)
        i += 1
        group_names.append(group_name)
        children[group_name] = {"hosts": hosts_dict}

    return group_names, inventory
