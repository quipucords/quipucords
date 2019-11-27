# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the user_data role."""

from scanner.network.processing import process


# pylint: disable=too-few-public-methods
class ProcessUserInfo(process.Processor):
    """Process the user_info fact."""

    KEY = 'user_info'

    DEPS = ['internal_user_info']
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        user_info = dependencies.get(
            'internal_user_info')
        if user_info and user_info.get('rc') == 0:
            result = [line for line in user_info.get(
                'stdout_lines') if line != '']
            return result
        return ''


class ProcessUserLoginHistory(process.Processor):
    """Process the user_login_history fact."""

    KEY = 'user_login_history'

    DEPS = ['internal_user_login_history']
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        user_login_history = dependencies.get(
            'internal_user_login_history')
        if user_login_history and user_login_history.get('rc') == 0:
            result = [line for line in user_login_history.get(
                'stdout_lines') if line != '']
            return result
        return ''


class ProcessUserDeleteHistory(process.Processor):
    """Process the user_delete_history fact."""

    KEY = 'user_delete_history'

    DEPS = ['internal_user_delete_history']
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        user_delete_history = dependencies.get(
            'internal_user_delete_history')
        if user_delete_history and user_delete_history.get('rc') == 0:
            result = [line for line in user_delete_history.get(
                'stdout_lines') if line != '']
            return result
        return ''
