# Copyright (c) 2017 Cloudistics, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):
    # Standard cloudistics documentation fragment
    DOCUMENTATION = '''
options:
  name:
    description:
      - Name of the application
    required: true
  wait:
    description:
      - Flag used to wait for action completion before returning
    required: false
    default: true
  wait_timeout:
    description:
      - time in seconds before wait returns
    required: false
    default: 60
requirements:
  - python >= 2.7
  - cloudistics >= 0.0.1
notes:
  - Authentication parameters such as API_KEY and ENDPOINT_* are not allowed in
    playbooks for security reasons. Please use `ccli setup` to create a configuration
    file.
  - Auth information is driven by the Cloudistics python library, which means that 
    values can come from an ini config file in /etc/cloudistics.conf or ~/.cloudistics,
    then finally from standard environment variables. More information can be found at
    U(https://http://cloudistics-python.readthedocs.org)
'''
