"""ScanTask used for network connection discovery."""

import logging
from contextlib import ExitStack
from functools import cached_property
from pathlib import Path

import ansible_runner
from ansible_runner.exceptions import AnsibleRunnerException
from django.conf import settings
from django.db import transaction
from django.forms import model_to_dict

import log_messages
from api.inspectresult.model import InspectGroup, RawFact
from api.models import (
    InspectResult,
    Scan,
    ScanTask,
    SystemConnectionResult,
)
from api.status.misc import get_server_id
from api.vault import write_to_yaml
from constants import GENERATED_SSH_KEYFILE, SCAN_JOB_LOG
from quipucords.environment import server_version
from scanner.exceptions import ScanFailureError
from scanner.network.exceptions import ScannerError
from scanner.network.inspect_callback import AnsibleResults, InspectCallback
from scanner.network.processing.process import NO_DATA, process
from scanner.network.utils import (
    construct_inventory,
    raw_facts_template,
)
from scanner.runner import ScanTaskRunner

logger = logging.getLogger(__name__)

DEFAULT_SCAN_DIRS = ["/", "/opt", "/app", "/home", "/usr"]
NETWORK_SCAN_IDENTITY_KEY = "connection_host"


class InspectTaskRunner(ScanTaskRunner):
    """InspectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        to store results
        """
        super().__init__(scan_job, scan_task)
        self.connect_scan_task = None

    def execute_task(self):
        """Scan target systems to collect facts.

        Attempts connections to a source using a list of credentials
        and gathers the set of successes (host/ip, credential) and
        failures (host/ip). Runs a host scan on the set of systems that are
        reachable. Collects the associated facts for the scanned systems
        """
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
                raise ScannerError(msg)

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
            # prepare ssh keys and format credential data
            credential_ssh_key: dict[int, str] = {}
            formatted_hosts = []
            with ExitStack() as stack:
                # ExitStack is required because we have a variable number of contexts.
                # Each unique credential will have its own ssh_keyfile, which will be
                # destroyed outside of this with block.
                for host_name, credential in remaining:
                    cred_data = model_to_dict(credential)
                    try:
                        ssh_keypath = credential_ssh_key[credential.id]
                    except KeyError:
                        ssh_keypath = stack.enter_context(
                            credential.generate_ssh_keyfile()
                        )
                        credential_ssh_key[credential.id] = ssh_keypath
                    cred_data[GENERATED_SSH_KEYFILE] = ssh_keypath
                    formatted_hosts.append(tuple((host_name, cred_data)))
                # finally, run the scan
                scan_message, scan_result = self._inspect_scan(formatted_hosts)

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

        except (AnsibleRunnerException, AssertionError, ScannerError) as error:
            error_message = f"Scan task encountered error: {error}"
            raise ScanFailureError(error_message)

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

        connected_hosts = set([system.get("name") for system in connected_hosts])
        scanned_hosts = set(
            [system.get(NETWORK_SCAN_IDENTITY_KEY) for system in systems_list]
        )
        unreachable_hosts = connected_hosts - scanned_hosts

        for host in unreachable_hosts:
            InspectResult.objects.create(
                name=host,
                status=InspectResult.UNREACHABLE,
                inspect_group=self._inspect_group,
            )

    def _inspect_scan(  # noqa: PLR0912, PLR0915, C901
        self, connected
    ):
        """Execute the host scan with the initialized source.

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
        connection_port = self.scan_task.source.port

        use_paramiko = self.scan_task.source.use_paramiko
        if use_paramiko is None:
            use_paramiko = False

        if self.scan_job.options is not None:
            forks = self.scan_job.options.get(Scan.MAX_CONCURRENCY)
            extra_vars = self.scan_job.get_extra_vars()
        else:
            forks = Scan.DEFAULT_MAX_CONCURRENCY
            extra_vars = Scan.get_default_extra_vars()

        if extra_vars.get(Scan.EXT_PRODUCT_SEARCH_DIRS) is None:
            extra_vars[Scan.EXT_PRODUCT_SEARCH_DIRS] = " ".join(DEFAULT_SCAN_DIRS)

        extra_vars["ansible_ssh_timeout"] = settings.QUIPUCORDS_SSH_INSPECT_TIMEOUT

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
            log_message = (
                f"START INSPECT PROCESSING GROUP {(idx + 1):d} of {len(group_names):d}"
            )
            self.scan_task.log_message(log_message)
            call = InspectCallback()

            # Build Ansible Runner Parameters
            job_timeout = int(settings.QUIPUCORDS_NETWORK_INSPECT_JOB_TIMEOUT) * len(
                group_names
            )
            runner_settings = {
                "idle_timeout": job_timeout,
                "job_timeout": job_timeout,
                "pexpect_timeout": 5,
            }
            playbook_path = str(
                settings.BASE_DIR / "scanner/network/runner/inspect.yml"
            )
            extra_vars["variable_host"] = group_name
            cmdline_list = []
            vault_file_path = f"--vault-password-file={settings.DJANGO_SECRET_PATH}"
            cmdline_list.append(vault_file_path)
            forks_cmd = f"--forks={forks}"
            cmdline_list.append(forks_cmd)
            if use_paramiko:
                cmdline_list.append("--connection=paramiko")
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
            except Exception:
                logger.exception("Uncaught exception during Ansible Runner execution")
                continue

            log_message = (
                "INSPECT PROCESSING GROUP ANSIBLE RUNNER COMPLETED"
                f" group {group_name}: {runner_obj.status=}"
                f" {runner_obj.rc=} {runner_obj.stats=}"
            )
            self.scan_task.log_message(log_message, log_level=logging.INFO)

            # persist facts
            for result in call.iter_results():
                self._persist_results(result)
            # save stdout and stderr from ansible
            self._persist_ansible_logs(runner_obj)
            self._persist_skipped_tasks(call)

            final_status = runner_obj.status
            if final_status == "canceled":
                msg = log_messages.NETWORK_PLAYBOOK_STOPPED % (
                    "INSPECT",
                    "canceled",
                )
                self.scan_task.log_message(msg)
            if final_status not in ["successful", "unreachable", "failed"]:
                if final_status == "timeout":
                    error_msg = log_messages.NETWORK_TIMEOUT_ERR
                else:
                    error_msg = log_messages.NETWORK_UNKNOWN_ERR
                # TODO: refactor this - this logic is incorrect. The result of
                # the whole scan is only taking into consideration the last group.
                scan_result = ScanTask.FAILED

            log_message = (
                "INSPECT PROCESSING GROUP COMPLETED"
                f" group {group_name}: {scan_result=}"
                f" {error_msg=}"
            )
            self.scan_task.log_message(log_message, log_level=logging.DEBUG)
        return error_msg, scan_result

    @transaction.atomic
    def _persist_results(self, ansible_results: AnsibleResults):
        facts = self._post_process_facts(ansible_results)
        self.scan_task.log_message(
            f"host scan complete for {ansible_results.host}."
            f" Status: {ansible_results.status}. Facts {facts}",
            log_level=logging.DEBUG,
        )
        sys_result = InspectResult.objects.create(
            name=ansible_results.host,
            status=ansible_results.status,
            inspect_group=self._inspect_group,
        )
        raw_facts = []
        for fact_key, fact_value in facts.items():
            raw_facts.append(
                RawFact(
                    name=fact_key,
                    value=fact_value,
                    inspect_result=sys_result,
                )
            )
        RawFact.objects.bulk_create(
            raw_facts, batch_size=settings.QUIPUCORDS_BULK_CREATE_BATCH_SIZE
        )
        increment_kwargs = self._get_scan_task_increment_kwargs(ansible_results.status)
        self.scan_task.increment_stats(ansible_results.host, **increment_kwargs)

    @cached_property
    def _inspect_group(self):
        inspect_group = InspectGroup.objects.create(
            source_type=self.scan_task.source.source_type,
            source_name=self.scan_task.source.name,
            server_id=get_server_id(),
            server_version=server_version(),
            source=self.scan_task.source,
        )
        inspect_group.tasks.add(self.scan_task)
        return inspect_group

    def _post_process_facts(self, ansible_results):
        logger.debug(
            "[host=%s] post processing facts. Unprocessed facts=%s",
            ansible_results.host,
            ansible_results.facts,
        )
        facts = {}
        for fact_key, fact_value in ansible_results.facts.items():
            try:
                processed_fact = process(
                    scan_task=self.scan_task,
                    previous_host_facts=facts,
                    fact_key=fact_key,
                    fact_value=fact_value,
                    host=ansible_results.host,
                )
            except Exception:
                logger.exception(
                    "[host=%s] Unexpected error ocurred during fact '%s' processing",
                    ansible_results.host,
                    fact_key,
                )
                continue
            if processed_fact == NO_DATA:
                processed_fact = None
            facts[fact_key] = processed_fact

        if settings.QUIPUCORDS_EXCLUDE_INTERNAL_FACTS:
            # remove internal facts before saving result
            facts = {
                fact_key: fact_value
                for fact_key, fact_value in facts.items()
                if not fact_key.startswith("internal_")
            }
        # # use templates as a boilerplate with "none" values
        final_facts = raw_facts_template()
        final_facts.update(facts)
        return final_facts

    def _get_scan_task_increment_kwargs(self, result):
        return {
            InspectResult.SUCCESS: {
                "increment_sys_scanned": True,
                "prefix": "CONNECTED",
            },
            InspectResult.FAILED: {
                "increment_sys_failed": True,
                "prefix": "FAILED",
            },
            InspectResult.UNREACHABLE: {
                "increment_sys_unreachable": True,
                "prefix": "UNREACHABLE",
            },
        }[result]

    def _persist_ansible_logs(self, runner_obj: ansible_runner.Runner):
        """Persist ansible logs."""
        for output in ["stdout", "stderr"]:
            output_path: Path = settings.LOG_DIRECTORY / SCAN_JOB_LOG.format(
                scan_job_id=self.scan_job.id,
                output_type=f"ansible-{output}",
            )
            with output_path.open("a") as file_obj:
                log_contents = getattr(runner_obj, output).read()
                if log_contents and not log_contents.endswith("\n"):
                    log_contents += "\n"
                file_obj.write(log_contents)

    def _persist_skipped_tasks(self, call: InspectCallback):
        """Persist a list of tasks that were skipped."""
        if not settings.QUIPUCORDS_FEATURE_FLAGS.is_feature_active(
            "REPORT_SKIPPED_TASKS"
        ):
            return

        output_path = (
            Path(settings.DEFAULT_DATA_DIR) / f"skipped-tasks-{self.scan_job.id}.txt"
        )
        skipped_everywhere = set.intersection(*call._skipped_facts.values())
        output_path.write_text("\n".join(sorted(skipped_everywhere)))

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
                connected.append(tuple((result.name, result.credential)))

        for result in self.scan_task.get_result():
            if result.status == InspectResult.SUCCESS:
                completed.append(result.name)
            elif result.status == InspectResult.FAILED:
                failed.append(result.name)
            elif result.status == InspectResult.UNREACHABLE:
                unreachable.append(result.name)
            else:
                nostatus.append(result.name)

        if bool(nostatus):
            invalid_state_msg = f"Results without a valid state: {', '.join(nostatus)}"
            self.scan_task.log_message(invalid_state_msg, log_level=logging.ERROR)

        return connected, completed, failed, unreachable
