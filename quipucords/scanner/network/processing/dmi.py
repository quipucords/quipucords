# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the dmi role."""

from scanner.network.processing import process


class ProcessDmiSystemUuid(process.Processor):
    """Process the dmi system uuid."""

    KEY = 'dmi_system_uuid'

    DEPS = ['internal_dmi_system_uuid']
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        dmi_system_uuid = dependencies.get('internal_dmi_system_uuid')
        if dmi_system_uuid and dmi_system_uuid.get('rc') == 0:
            result = dmi_system_uuid.get('stdout_lines')
            if result:
                if result[0] == '' and len(result) > 1:
                    return result[1]
                return result[0]
        return ''
