#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project and Cloudistics Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cl_instance_facts
extends_documentation_fragment: cloudistics
short_description: Gather facts about applications in Cloudistics
description:
    - Gather facts about applications in Cloudistics
version_added: "2.4"
options:
  instance_names:
    description:
      - If you specify one or more instance names, only instances that have the specified names are returned.
    required: false
    version_added: 2.5
  instance_uuids:
    description:
      - If you specify one or more instance UUIDs, only instances that have the specified UUIDs are returned.
    required: false
    version_added: 2.5
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. Filter
        names and values are case sensitive.
    required: false
    default: {}
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Cloudistics Guide for details.

# Gather facts about all applications
- cl_app_facts:

# Gather facts about all applications in VDC test-vdc
- cl_app_facts:
    filters:
      data_center: test-vdc

# Gather facts about a particular application using its UUID
- cl_app_facts:
    instance_uuids:
      - aa0f885b-f434-414e-8d6a-86b39529ef6d

# Gather facts about a particular application using its name
- cl_app_facts:
    instance_names:
      - test01

'''

RETURN = '''
instances:
    description: a list of Cloudistics applications
    returned: always
    type: complex
    contains:
        name:
            description: Name of the application
            returned: always
            type: string
            sample: test01
        uuid:
            description: UUID of the application
            returned: always
            type: string
            sample: aa0f885b-f434-414e-8d6a-86b39529ef6d
        description:
            description: Description of the application
            returned: always
            type: string
            sample: This application was created from a CentOS template.
        vcpus:
            description: Count of vcpus to be assigned to the new application
            returned: always
            type: int
            sample: 4
        memory:
            description: Amount of memory to be assigned to the new application (kb, mb, gb, tb. e.g., 1g)
            returned: always
            type: int
            sample: 1073741824
        data_center_uuid:
            description: Data center UUID of the application
            returned: always
            type: string
            sample: 101552a2-e436-415a-a1cd-a11e5cb1e06e
'''

import logging

try:
    import cloudistics
    from cloudistics import ApplicationsManager
    from cloudistics import exceptions

    HAS_CL = True
except ImportError as e:
    HAS_CL = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudistics import cloudistics_full_argument_spec
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

FILTERS = ['data_center', 'application_group']


def list_instances(a_module):
    instance_names = a_module.params.get("instance_names")
    instance_uuids = a_module.params.get("instance_uuids")
    filters = a_module.params.get("filters")

    try:
        app_mgr = ApplicationsManager(cloudistics.client(api_key=a_module.params.get('api_key')))

        applications = []
        if len(instance_names) or len(instance_uuids):
            # Filtering by names/uuids, call for them
            for instance_name in instance_names:
                applications.append(app_mgr.detail(instance_name))
            for instance_uuid in instance_uuids:
                applications.append(app_mgr.detail(instance_uuid))
        else:
            if filters:
                dc_ids = []
                ag_ids = []
                if 'data_center' in filters:
                    dc_ids.append(filters['data_center'])
                if 'application_group' in filters:
                    ag_ids.append(filters['application_group'])

                instances = app_mgr.list(datacenter_ids=tuple(dc_ids), application_group_ids=tuple(ag_ids))
            else:
                instances = app_mgr.list(limit=2)

            for instance in instances:
                applications.append(camel_dict_to_snake_dict(app_mgr.detail(instance['uuid'])))

        a_module.exit_json(instances=applications)
    except exceptions.CloudisticsAPIError as e:
        a_module.fail_json(msg=e.message)


def main():
    argument_spec = cloudistics_full_argument_spec(
        instance_names=dict(default=[], type='list'),
        instance_uuids=dict(default=[], type='list'),
        filters=dict(default={}, type='dict')
    )

    a_module = AnsibleModule(
        argument_spec=argument_spec,

        mutually_exclusive=[
            ['instance_names', 'filters'],
            ['instance_uuids', 'filters']
        ],

        supports_check_mode=False
    )

    if not a_module.no_log:
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        if a_module._debug:
            logger.setLevel(logging.DEBUG)

    if not HAS_CL:
        a_module.fail_json(msg='Cloudistics python library required for this module')

    list_instances(a_module)


if __name__ == '__main__':
    main()
