"""ScanTask used for network connection discovery."""
import logging
import os.path
from multiprocessing import Value

import ansible_runner
import pexpect
from ansible_runner.exceptions import AnsibleRunnerException
from django.conf import settings
from django.db import transaction
from django.forms import model_to_dict

import log_messages
from api.models import (
    Credential,
    ScanJob,
    ScanOptions,
    ScanTask,
    SystemConnectionResult,
)
from api.serializers import SourceSerializer
from api.vault import decrypt_data_as_unicode, write_to_yaml
from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.utils import (
    check_manager_interrupt,
    construct_inventory,
    expand_hostpattern,
)
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)


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
            message = f"{name} with {credential.name}"
            self.scan_task.increment_stats(
                message, increment_sys_scanned=True, prefix="CONNECTED"
            )
        elif status == SystemConnectionResult.UNREACHABLE:
            message = f"{name} is UNREACHABLE"
            self.scan_task.increment_stats(
                message, increment_sys_unreachable=True, prefix="FAILED"
            )
        else:
            if credential is not None:
                message = f"{name} with {credential.name}"
            else:
                message = f"{name} has no valid credentials"

            self.scan_task.increment_stats(
                message, increment_sys_failed=True, prefix="FAILED"
            )

        self._remaining_hosts.remove(name)

    def remaining_hosts(self):
        """Get the set of hosts that are left to scan."""
        # Need to return a list because the caller can iterate over
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

    supports_partial_results = False

    def execute_task(self, manager_interrupt: Value):
        """Scan network range and attempt connections.

        :param manager_interrupt: Synchronized Value which can inform
        a task of the need to shut down immediately
        """
        result_store = ConnectResultStore(self.scan_task)
        scan_message, scan_result = self.run_with_result_store(
            manager_interrupt, result_store
        )
        return scan_message, scan_result

    def run_with_result_store(
        self, manager_interrupt: Value, result_store: ConnectResultStore
    ):
        """Run with a given ConnectResultStore.

        :param manager_interrupt: Synchronized Value which can inform
        a task of the need to shut down immediately
        :param result_store: ConnectResultStore
        """
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
            check_manager_interrupt(manager_interrupt)
            credential = Credential.objects.get(pk=cred_id)
            if not remaining_hosts:
                message = f"Skipping credential {credential.name}. No remaining hosts."
                self.scan_task.log_message(message)
                break

            message = f"Attempting credential {credential.name}."
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
                    f"Connect scan task failed with credential {credential.name}."
                    f" Error: {ansible_error} Hosts: {remaining_hosts_str}"
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


def _connect(  # noqa: PLR0913, PLR0912, PLR0915
    manager_interrupt: Value,
    scan_task: ScanTask,
    hosts,
    result_store: ConnectResultStore,
    credential,
    connection_port,
    forks,
    use_paramiko=False,
    exclude_hosts=None,
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
    :returns: list of connected hosts credential tuples and
            list of host that failed connection
    """
    cred_data = model_to_dict(credential)
    group_names, inventory = construct_inventory(
        hosts=hosts,
        credential=cred_data,
        connection_port=connection_port,
        concurrency_count=forks,
        exclude_hosts=exclude_hosts,
    )
    inventory_file = write_to_yaml(inventory)
    _handle_ssh_passphrase(cred_data)

    log_message = (
        "START CONNECT PROCESSING GROUPS"
        f" with use_paramiko: {use_paramiko} and {forks:d} forks"
    )
    scan_task.log_message(log_message)
    for idx, group_name in enumerate(group_names):
        check_manager_interrupt(manager_interrupt)
        group_ips = (
            inventory.get("all").get("children").get(group_name).get("hosts").keys()
        )
        group_ips = [f"'{ip}'" for ip in group_ips]
        group_ip_string = ", ".join(group_ips)
        log_message = (
            f"START CONNECT PROCESSING GROUP {(idx + 1):d} of {len(group_names):d}. "
            f"About to connect to hosts [{group_ip_string}]"
        )
        scan_task.log_message(log_message)
        call = ConnectResultCallback(
            result_store, credential, scan_task.source, manager_interrupt
        )

        # Create parameters for ansible runner
        runner_settings = {"job_timeout": int(settings.NETWORK_CONNECT_JOB_TIMEOUT)}
        extra_vars_dict = {
            "variable_host": group_name,
            "ansible_ssh_timeout": settings.QPC_SSH_CONNECT_TIMEOUT,
        }
        playbook_path = os.path.join(
            settings.BASE_DIR, "scanner/network/runner/connect.yml"
        )
        cmdline_list = []
        vault_file_path = f"--vault-password-file={settings.DJANGO_SECRET_PATH}"
        cmdline_list.append(vault_file_path)
        forks_cmd = f"--forks={forks}"
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
        except Exception as err_msg:  # noqa: BLE001
            raise AnsibleRunnerException(err_msg) from err_msg

        final_status = runner_obj.status
        if final_status == "canceled":
            if (
                manager_interrupt
                and manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL
            ):
                msg = log_messages.NETWORK_PLAYBOOK_STOPPED % (
                    "CONNECT",
                    "canceled",
                )
                return msg, scan_task.CANCELED
            msg = log_messages.NETWORK_PLAYBOOK_STOPPED % ("CONNECT", "paused")
            return msg, scan_task.PAUSED
        if final_status not in ["successful", "unreachable", "failed", "canceled"]:
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
    """Attempt to set up login via passphrase if necessary.

    :param credential: The credential used for connections
    """
    if (
        credential.get("ssh_keyfile") is not None
        and credential.get("ssh_passphrase") is not None
    ):
        keyfile = credential.get("ssh_keyfile")
        passphrase = decrypt_data_as_unicode(credential["ssh_passphrase"])
        cmd_string = f"ssh-add {keyfile}"

        try:
            child = pexpect.spawn(cmd_string, timeout=12)
            phrase = [pexpect.EOF, "Enter passphrase for .*:"]
            i = child.expect(phrase)
            while i:
                child.sendline(passphrase)
                i = child.expect(phrase)
        except pexpect.exceptions.TIMEOUT:
            pass
