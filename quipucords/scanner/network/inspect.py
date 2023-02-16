"""ScanTask used for network connection discovery."""
import logging
import os.path

import ansible_runner
from ansible_runner.exceptions import AnsibleRunnerException
from django.conf import settings

import log_messages
from api.credential.serializer import CredentialSerializer
from api.models import (
    ScanJob,
    ScanOptions,
    ScanTask,
    SystemConnectionResult,
    SystemInspectionResult,
)
from api.vault import write_to_yaml
from scanner.exceptions import ScanFailureError
from scanner.network.exceptions import ScannerException
from scanner.network.inspect_callback import InspectResultCallback
from scanner.network.utils import check_manager_interrupt, construct_inventory
from scanner.task import ScanTaskRunner

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

DEFAULT_SCAN_DIRS = ["/", "/opt", "/app", "/home", "/usr"]
NETWORK_SCAN_IDENTITY_KEY = "connection_host"


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        to store results
        """
        super().__init__(scan_job, scan_task, supports_partial_results=True)
        self.connect_scan_task = None

    def execute_task(self, manager_interrupt):
        """Scan target systems to collect facts.

        Attempts connections to a source using a list of credentials
        and gathers the set of successes (host/ip, credential) and
        failures (host/ip). Runs a host scan on the set of systems that are
        reachable. Collects the associated facts for the scanned systems
        """
        # pylint: disable=too-many-locals

        self.connect_scan_task = self.scan_task.prerequisites.first()
        if self.connect_scan_task.status != ScanTask.COMPLETED:
            error_message = (
                f"Prerequisites scan task {self.connect_scan_task.sequence_number}"
                f" failed."
            )
            return error_message, ScanTask.FAILED

        try:
            # Execute scan
            connected, completed, failed, unreachable = self._obtain_discovery_data()
            processed_hosts = failed + completed
            num_total = len(connected) + len(processed_hosts)

            if num_total == 0:
                msg = "Inventory provided no reachable hosts."
                raise ScannerException(msg)

            self.scan_task.update_stats(
                "INITIAL NETWORK INSPECT STATS",
                sys_count=len(connected),
                sys_scanned=len(completed),
                sys_failed=len(failed),
                sys_unreachable=len(unreachable),
            )

            # remove completed hosts
            remaining = [
                unprocessed
                for unprocessed in connected
                if unprocessed[0] not in processed_hosts
            ]
            scan_message, scan_result = self._inspect_scan(manager_interrupt, remaining)

            self.scan_task.cleanup_facts(NETWORK_SCAN_IDENTITY_KEY)
            temp_facts = self.scan_task.get_facts()
            fact_size = len(temp_facts)
            self._add_unreachable_hosts(temp_facts)
            if temp_facts is None or fact_size == 0:
                msg = (
                    "SystemFacts set is empty. "
                    "No results will be reported to fact endpoint."
                )
                raise ScanFailureError(msg)

        except (AnsibleRunnerException, AssertionError, ScannerException) as error:
            error_message = f"Scan task encountered error: {error}"
            raise ScanFailureError(error_message)  # pylint: disable=raise-missing-from

        if self.scan_task.systems_failed > 0:
            scan_message = (
                f"{self.scan_task.systems_failed} systems could not be scanned."
            )
            scan_result = ScanTask.COMPLETED
            self.scan_task.log_message(scan_message, log_level=logging.WARNING)
        return scan_message, scan_result

    def _add_unreachable_hosts(self, systems_list):
        """Add entry for systems that were unreachable.

        :param systems_list: Current list of system results.
        """
        connected_hosts = self.connect_scan_task.connection_result.systems.filter(
            status=SystemConnectionResult.SUCCESS
        ).values("name")
        # pylint: disable=consider-using-set-comprehension
        connected_hosts = set([system.get("name") for system in connected_hosts])
        scanned_hosts = set(
            [system.get(NETWORK_SCAN_IDENTITY_KEY) for system in systems_list]
        )
        unreachable_hosts = connected_hosts - scanned_hosts

        for host in unreachable_hosts:
            sys_result = SystemInspectionResult(
                name=host,
                status=SystemInspectionResult.UNREACHABLE,
                source=self.scan_task.source,
                task_inspection_result=self.scan_task.inspection_result,
            )
            sys_result.save()

    def _inspect_scan(self, manager_interrupt, connected):
        """Execute the host scan with the initialized source.

        :param manager_interrupt: Signal used to communicate termination
            of scan
        :param connected: list of (host, credential) pairs to inspect
        :param base_ssh_executable: ssh executable, or None for
            'ssh'. Will be wrapped with a timeout before being passed
            to Ansible.
        :param ssh_timeout: string in the format of the 'timeout'
            command. Timeout for individual tasks.
        :returns: An array of dictionaries of facts

        Note: base_ssh_executable & ssh_timeout are parameters that
        are only used for testing.
        """
        # pylint: disable=too-many-locals,too-many-arguments
        # pylint: disable=too-many-branches,too-many-statements
        connection_port = self.scan_task.source.port

        if self.scan_task.source.options is not None:
            use_paramiko = self.scan_task.source.options.use_paramiko
        else:
            use_paramiko = False

        if self.scan_job.options is not None:
            forks = self.scan_job.options.max_concurrency
            extra_vars = self.scan_job.options.get_extra_vars()
        else:
            forks = ScanOptions.get_default_forks()
            extra_vars = ScanOptions.get_default_extra_vars()

        if extra_vars.get(ScanOptions.EXT_PRODUCT_SEARCH_DIRS) is None:
            extra_vars[ScanOptions.EXT_PRODUCT_SEARCH_DIRS] = " ".join(
                DEFAULT_SCAN_DIRS
            )

        extra_vars.update(
            {
                "QPC_FEATURE_FLAGS": settings.QPC_FEATURE_FLAGS.as_dict(),
                "ansible_ssh_timeout": settings.QPC_SSH_INSPECT_TIMEOUT,
                "ansible_ssh_extra_args": "-o SetEnv='LC_ALL=C",
                "ansible_shell_executable": "/bin/sh",
            }
        )

        group_names, inventory = construct_inventory(
            hosts=connected,
            connection_port=connection_port,
            concurrency_count=forks,
        )
        inventory_file = write_to_yaml(inventory)

        error_msg = None
        log_message = (
            "START INSPECT PROCESSING GROUPS"
            f" with use_paramiko: {use_paramiko}, "
            f"{forks} forks and extra_vars={extra_vars}"
        )
        self.scan_task.log_message(log_message)
        scan_result = ScanTask.COMPLETED

        # Build Ansible Runner Dependencies
        for idx, group_name in enumerate(group_names):
            check_manager_interrupt(manager_interrupt.value)
            log_message = (
                "START INSPECT PROCESSING GROUP"
                f" {(idx + 1):d} of {len(group_names):d}"
            )
            self.scan_task.log_message(log_message)
            call = InspectResultCallback(self.scan_task, manager_interrupt)

            # Build Ansible Runner Parameters
            runner_settings = {
                "idle_timeout": int(settings.NETWORK_INSPECT_JOB_TIMEOUT),
                "job_timeout": int(settings.NETWORK_INSPECT_JOB_TIMEOUT),
                "pexpect_timeout": 5,
            }
            playbook_path = os.path.join(
                settings.BASE_DIR, "scanner/network/runner/inspect.yml"
            )
            extra_vars["variable_host"] = group_name
            cmdline_list = []
            vault_file_path = f"--vault-password-file={settings.DJANGO_SECRET_PATH}"
            cmdline_list.append(vault_file_path)
            forks_cmd = f"--forks={forks}"
            cmdline_list.append(forks_cmd)
            if use_paramiko:
                cmdline_list.append("--connection=paramiko")
            else:
                cmdline_list.append("--connection=ssh")
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
                    extravars=extra_vars,
                    event_handler=call.event_callback,
                    cancel_callback=call.cancel_callback,
                    playbook=playbook_path,
                    cmdline=all_commands,
                    verbosity=verbosity_lvl,
                )
            except Exception as error:
                logger.exception("Unexpected error")
                raise AnsibleRunnerException(str(error)) from error

            final_status = runner_obj.status
            if final_status != "successful":
                if final_status == "canceled":
                    interrupt = manager_interrupt.value
                    if interrupt == ScanJob.JOB_TERMINATE_CANCEL:
                        msg = log_messages.NETWORK_PLAYBOOK_STOPPED % (
                            "INSPECT",
                            "canceled",
                        )
                    else:
                        msg = log_messages.NETWORK_PLAYBOOK_STOPPED % (
                            "INSPECT",
                            "paused",
                        )
                    self.scan_task.log_message(msg)
                    check_manager_interrupt(interrupt)
                if final_status not in ["unreachable", "failed"]:
                    if final_status == "timeout":
                        error_msg = log_messages.NETWORK_TIMEOUT_ERR
                    else:
                        error_msg = log_messages.NETWORK_UNKNOWN_ERR
                    scan_result = ScanTask.FAILED

            # Always run this as our scans are more tolerant of errors
            call.finalize_failed_hosts()
        return error_msg, scan_result

    def _obtain_discovery_data(self):
        """Obtain discover scan data.  Either via new scan or paused scan.

        :returns: List of connected, inspection failed, and
        inspection completed.
        """
        connected = []
        failed = []
        completed = []
        unreachable = []
        nostatus = []
        for result in self.connect_scan_task.connection_result.systems.all():
            if result.status == SystemConnectionResult.SUCCESS:
                host_cred = result.credential
                serializer = CredentialSerializer(host_cred)
                connected.append((result.name, serializer.data))

        for result in self.scan_task.inspection_result.systems.all():
            if result.status == SystemInspectionResult.SUCCESS:
                completed.append(result.name)
            elif result.status == SystemInspectionResult.FAILED:
                failed.append(result.name)
            elif result.status == SystemInspectionResult.UNREACHABLE:
                unreachable.append(result.name)
            else:
                nostatus.append(result.name)

        if bool(nostatus):
            invalid_state_msg = f"Results without a valid state: {', '.join(nostatus)}"
            self.scan_task.log_message(invalid_state_msg, log_level=logging.ERROR)

        return connected, completed, failed, unreachable
