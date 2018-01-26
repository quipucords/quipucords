# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Defining the set of facts that Sonar should scan for."""


def expand_facts(dict):
    new_dict = {'jboss_eap': False,
                'jboss_fuse': False,
                'jboss_brms': False}
    if dict['jboss-fuse']:
        new_dict['jboss_eap'] = True
        new_dict['jboss_fuse'] = True
    elif dict['jboss-brms']:
        new_dict['jboss_eap'] = True
        new_dict['jboss_brms'] = True
    elif dict['jboss-eap']:
        new_dict['jboss_eap'] = True

    return new_dict