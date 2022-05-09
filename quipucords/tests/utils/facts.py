# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Helpers to handle facts."""


def fact_expander(fact_name):
    """Expand a fact name to cover all "parent" facts."""
    vals = set(fact_name.split("/"))
    return {fact.split("__")[0] for fact in vals}
