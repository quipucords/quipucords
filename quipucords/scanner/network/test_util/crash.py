#!/usr/bin/env python3
#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""A program to simulate crashes in an SSH session."""

import sys


if __name__ == "__main__":
    # 'man ssh' says ssh exits with 255 if an error occurs.
    sys.exit(255)
