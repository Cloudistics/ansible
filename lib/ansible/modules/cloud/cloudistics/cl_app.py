#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cl_app
short_description: Create/Delete Applications from Cloudistics
extends_documentation_fragment: cloudistics
description:
   - Creates or Removes Cloudistics virtual machines.
options:
  description:
    description:
      - Description of the application
    required: false
  vcpus:
    description:
      - Count of vcpus to be assigned to the new application
    required: false
  memory:
    description:
      - Amount of memory to be assigned to the new application (kb, mb, gb, tb. e.g., 1g)
    required: false
  tags:
    description:
      - Tag or list of tags to be provided to the application
    required: false
  template:
    description:
      - Template to create the application with
    required: false
  category:
    description:
      - Category to create this application with
    required: false
  data_center:
    description:
      - Data center to create this application into
    required: false
  migration_zone:
    description:
      - Migration zone to create this application with
    required: false
  flash_pool:
    description:
      - Flash pool to create this application with
    required: false
  vnic_name:
    description:
      - Virtual NIC Name
    required: false
  vnic_mode:
    description:
      - Virtual NIC Mode
    required: false
    default: 'Bridged'
    choices: ['Bridged', 'Node-Only', 'Virtual Networking']
  vnic_vnet:
    description:
      - Virtual NIC VNET
    required: false
  vnic_fw:
    description:
      - Virtual NIC FW
    required: false
  vnic_mac:
    description:
      - Virtual NIC MAC Address
    required: false
  state:
    description:
      - Should the resource be present or absent.
    required: true
    default: present
    choices: [absent, present]
'''

EXAMPLES = '''
- name: Build application
  hosts: localhost
  gather_facts: False
  tasks:
  - name: Build instance request
    cl_app:
      name: xx
      description: xx
      vcpus: 1
      memory: 1073741824
      template: World Community Grid
      category: Default
      data_center: DC2
      migration_zone: MZ1
      flash_pool: SP1
      vnic_name: 'vNIC 0'
      vnic_mode: 'Virtual Networking'
      vnic_vnet: Vnet1
      vnic_fw: 'allow all'
      tags:
        - TT1
        - TT2
      wait: False
      state: present

- name: Build additional instances
  hosts: localhost
  gather_facts: False
  tasks:
  - name: Build instances request
    cl_app:
      name: "{{ item.name }}"
      description: "{{ item.description }}"
      vcpus: "{{ item.vcpu }}"
      memory: "{{ item.memory }}"
      template: "{{ item.template }}"
      category: "{{ item.category }}"
      data_center: "{{ item.data_center }}"
      migration_zone: "{{ item.migration_zone }}"
      flash_pool: "{{ item.flash_pool }}"
      tags: "{{ item.tags }}"
      wait: "{{ item.wait }}"
    with_items:
      - name: xx1
        description: xx
        vcpus: 1
        memory: 1073741824
        template: World Community Grid
        category: Default
        data_center: DC2
        migration_zone: MZ1
        flash_pool: SP1
        vnic_name: 'vNIC 0'
        vnic_mode: 'Virtual Networking'
        vnic_vnet: Vnet1
        vnic_fw: 'allow all'
        tags:
          - TT1
          - TT2
        wait: True
      - name: xx2
        description: xx
        vcpus: 1
        memory: 1073741824
        template: World Community Grid
        category: Default
        data_center: DC2
        migration_zone: MZ1
        flash_pool: SP1
        vnic_name: 'vNIC 0'
        vnic_mode: 'Virtual Networking'
        vnic_vnet: Vnet1
        vnic_fw: 'allow all'
        tags:
          - TT1
          - TT2
        wait: True
      - name: xx3
        description: xx
        vcpus: 1
        memory: 1073741824
        template: World Community Grid
        category: Default
        data_center: DC2
        migration_zone: MZ1
        flash_pool: SP1
        vnic_name: 'vNIC 0'
        vnic_mode: 'Virtual Networking'
        vnic_vnet: Vnet1
        vnic_fw: 'allow all'
        tags:
          - TT1
          - TT2
        wait: True

- name: Cancel instances
  hosts: localhost
  gather_facts: False
  tasks:
  - name: Cancel by name
    cl_app:
      state: absent
      name: xx1
'''

# from __future__ import absolute_import, division, print_function

import json

try:
    import cloudistics
    from cloudistics import ActionsManager, ApplicationsManager, exceptions

    HAS_CL = True
except ImportError:
    HAS_CL = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudistics import cloudistics_convert_memory_abbreviation_to_bytes
from ansible.module_utils.cloudistics import cloudistics_full_argument_spec
from ansible.module_utils.cloudistics import cloudistics_lookup_by_name
from ansible.module_utils.cloudistics import cloudistics_wait_for_action

STATES = ['absent', 'present']
MODES = ['Bridged', 'Node-Only', 'Virtual Networking']


def main():
    argument_spec = cloudistics_full_argument_spec(
        state=dict(required='present', choices=STATES),
        description=dict(),
        vcpus=dict(type='int', aliases=['cpus', 'vcpu', 'cpu']),
        memory=dict(default=1073741824, aliases=['mem']),
        template=dict(),
        category=dict(aliases=['cat']),
        data_center=dict(aliases=['dc']),
        migration_zone=dict(aliases=['mz']),
        flash_pool=dict(aliases=['fp', 'sp']),
        vnic_name=dict(),
        vnic_mode=dict(default='Bridged', choices=MODES),
        vnic_vnet=dict(),
        vnic_fw=dict(),
        vnic_mac=dict(),
        tags=dict(type='list'),
    )

    a_module = AnsibleModule(
        argument_spec=argument_spec,

        mutually_exclusive=(
            ['name', 'uuid'],
        ),

        required_if=(
            [
                # ['state', 'absent', ['name']],
                ['state', 'present', ['name', 'template', 'data_center', 'migration_zone', 'flash_pool']],
                ['vnic_mode', 'Virtual Networking', ['vnic_vnet']]
            ]
        ),

        required_one_of=[
            ['name', 'uuid']
        ],

        # required_together=(
        #     ['a', 'b', 'b'],
        # ),

        supports_check_mode=True
    )

    state = a_module.params['state']
    wait = a_module.params['wait']
    wait_timeout = a_module.params['wait_timeout']

    changed = False
    completed = False
    status = None

    if not HAS_CL:
        a_module.fail_json(msg='Cloudistics python library (>=0.9.4) required for this module')

    try:
        act_mgr = ActionsManager(cloudistics.client())
        app_mgr = ApplicationsManager(cloudistics.client())
        instance = cloudistics_lookup_by_name(app_mgr, a_module.params.get('name'), a_module.params.get('uuid'))

        if a_module.check_mode:
            if state == 'absent':
                a_module.exit_json(instance=instance, changed=(instance is not None))
            elif state == 'present':
                a_module.exit_json(instance=instance, changed=(instance is None))

        if state == 'absent' and instance:
            uuid_to_delete = instance['uuid']
            res_action = app_mgr.delete(uuid_to_delete)
            if res_action:
                changed = True
                if wait:
                    (completed, status) = cloudistics_wait_for_action(act_mgr, wait_timeout, res_action)
                instance = cloudistics_lookup_by_name(app_mgr, a_module.params.get('name'), a_module.params.get('uuid'))

        elif state == 'present' and not instance:
            mem_in_bytes = cloudistics_convert_memory_abbreviation_to_bytes(a_module.params.get('memory'))
            res_action = app_mgr.create(
                name=a_module.params.get('name'),
                description=a_module.params.get('description'),
                vcpus=a_module.params.get('vcpus'),
                memory=mem_in_bytes,
                template_name_or_uuid=a_module.params.get('template'),
                cat_name_or_uuid=a_module.params.get('category'),
                dc_name_or_uuid=a_module.params.get('data_center'),
                mz_name_or_uuid=a_module.params.get('migration_zone'),
                fp_name_or_uuid=a_module.params.get('flash_pool'),
                # vnic_name=a_module.params.get('vnic_name'),
                # vnic_mode=a_module.params.get('vnic_mode'),
                vnic_vnet_name_or_uuid=a_module.params.get('vnic_vnet'),
                vnic_firewall_name_or_uuid=a_module.params.get('vnic_fw'),
                vnic_mac_address=a_module.params.get('vnic_mac_address'))
            if res_action:
                changed = True
                if wait:
                    (completed, status) = cloudistics_wait_for_action(act_mgr, wait_timeout, res_action)
                instance = app_mgr.detail(res_action['objectUuid'])

        a_module.exit_json(changed=changed,
                           completed=completed,
                           instance=json.loads(json.dumps(instance, default=lambda o: o.__dict__)),
                           status=status)
    except exceptions.CloudisticsAPIError as e:
        a_module.fail_json(msg=e.message)

    # except TypeError as e:
    #     a_module.fail_json(msg=str(e))

    except ValueError as e:
        a_module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
