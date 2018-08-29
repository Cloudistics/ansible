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
  api_key:
    description:
      - API key to use
    required: false
version_added: "2.5"
author: 
- Joe Cavanaugh (@juniorfoo)
requirements:
  - python >= 2.7
  - cloudistics >= 3.5.1
notes:
  - Auth information is driven by the Cloudistics python library, which means that 
    values can come from the playbook, an ini config file in /etc/cloudistics.conf 
    or ~/.cloudistics, or from standard environment variables. More information can be found at
    U(https://http://cloudistics-python.readthedocs.org)
'''
