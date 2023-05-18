"""ScanTask used for vcenter connection task."""
import logging
from socket import gaierror

from pyVmomi import vim, vmodl  # pylint: disable=no-name-in-module

from api.models import ScanTask, SystemConnectionResult
from scanner.runner import ScanTaskRunner
from scanner.vcenter.utils import retrieve_properties, vcenter_connect

logger = logging.getLogger(__name__)


def get_vm_names(content):
    """Get the vm names from the container view.

    :param vm_container_view: The VM container view.
    :returns: list of vm names.
    """
    vm_names = []

    visit_folders = vmodl.query.PropertyCollector.TraversalSpec(
        name="visitFolders", type=vim.Folder, path="childEntity", skip=False
    )

    visit_folders.selectSet.extend(
        [
            vmodl.query.PropertyCollector.SelectionSpec(name="visitFolders"),
            vmodl.query.PropertyCollector.SelectionSpec(name="dcToVmFolder"),
        ]
    )

    dc_to_vm_folder = vmodl.query.PropertyCollector.TraversalSpec(
        name="dcToVmFolder", type=vim.Datacenter, path="vmFolder", skip=False
    )
    dc_to_vm_folder.selectSet.extend(
        [vmodl.query.PropertyCollector.SelectionSpec(name="visitFolders")]
    )

    filter_spec = vmodl.query.PropertyCollector.FilterSpec(
        objectSet=[
            vmodl.query.PropertyCollector.ObjectSpec(
                obj=content.rootFolder,
                skip=False,
                selectSet=[visit_folders, dc_to_vm_folder],
            ),
        ],
        propSet=[
            vmodl.query.PropertyCollector.PropertySpec(
                all=False,
                type=vim.VirtualMachine,
                pathSet=["name"],
            ),
        ],
    )

    objects = retrieve_properties(content, [filter_spec])
    for object_content in objects:
        vm_names.append(object_content.propSet[0].val)

    return vm_names


class ConnectTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner vcenter connection capabilities.

    Attempts connections to a source using a credential
    and gathers the set of available virtual systems.
    """

    supports_partial_results = False

    def _store_connect_data(self, connected, credential, source):
        # Update the scan counts
        self.scan_task.update_stats(
            "INITIAL VCENTER CONNECT STATS.", sys_count=len(connected)
        )

        for system in connected:
            sys_result = SystemConnectionResult(
                name=system,
                status=SystemConnectionResult.SUCCESS,
                credential=credential,
                source=source,
                task_connection_result=self.scan_task.connection_result,
            )
            sys_result.save()
            self.scan_task.increment_stats(sys_result.name, increment_sys_scanned=True)

        self.scan_task.connection_result.save()

    def execute_task(self, manager_interrupt):
        """Scan vcenter and attempt connections."""
        source = self.scan_task.source
        credential = self.scan_task.source.credentials.all().first()
        try:
            connected = self.connect()
            self._store_connect_data(connected, credential, source)
        except vim.fault.InvalidLogin as vm_error:
            error_message = (
                f"Unable to connect to VCenter source, {source.name},"
                f" with supplied credential, {credential.name}.\n"
            )
            error_message += f"Connect scan failed for {self.scan_task}. {vm_error}"
            return error_message, ScanTask.FAILED
        except gaierror as error:
            error_message = f"Unable to connect to VCenter source {source.name}%s.\n"
            error_message += f"Reason for failure: {error}"
            return error_message, ScanTask.FAILED

        return None, ScanTask.COMPLETED

    # pylint: disable=too-many-locals
    def connect(self):
        """Execute the connect scan with the initialized source.

        :returns: list of connected vm credential tuples
        """
        vm_names = []

        vcenter = vcenter_connect(self.scan_task)
        content = vcenter.RetrieveContent()
        vm_names = get_vm_names(content)

        return vm_names
