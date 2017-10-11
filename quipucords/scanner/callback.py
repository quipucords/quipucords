#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Scanner used for host connection discovery"""

from ansible.plugins.callback import CallbackBase


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    def __init__(self, display=None):
        super().__init__(display=display)
        self.results = []

    def v2_runner_on_ok(self, result):
        """Print a json representation of the result
        """
        # pylint: disable=protected-access
        host = result._host
        self.results.append({'host': host.name, 'result': result._result})

    def v2_runner_on_unreachable(self, result):
        """Print a json representation of the result
        """
        # pylint: disable=protected-access
        host = result._host
        self.results.append({'host': host.name, 'result': result._result})

    def v2_runner_on_failed(self, result, ignore_errors=False):
        # pylint: disable=protected-access
        host = result._host
        self.results.append({'host': host.name, 'result': result._result})
