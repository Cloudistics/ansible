#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cl_app
short_description: Create/Delete Applications from Cloudistics
extends_documentation_fragment: cloudistics
version_added: "2.4"
author: "Joe Cavanaugh (@juniorfoo)"
description:
   - Create or Remove applications from Cloudistics.
options:
  description:
    description:
      - Description of the application
    required: false
    default: null
  vcpus:
    description:
      - Count of vcpus to be assigned to the new application
    required: false
    default: null
  memory:
    description:
      - Amount of memory to be assigned to the new application
    required: false
    default: null
  tags:
    description:
      - Tag or list of tags to be provided to the application
    required: false
    default: null
  template_name:
    description:
      - Name of the template to create the application with
    required: false
    default: true
  category_name:
    description:
      - Name of the category to create this application with
    required: false
    default: false
  data_center_name:
    description:
      - Name of the data center to create this application into
    required: false
    default: false
  migration_zone_name:
    description:
      - Name of the migration zone to create this application with
    required: false
    default: true
  flash_pool_name:
    description:
      - Name of the flash pool to create this application with
    required: true
    default: null
  nics:
    description:
      - List of nics for this application (see example)
    required: true
    default: null
  state:
    description:
      - Should the resource be present or absent.
    required: true
    default: 'present'
    choices: ['present', 'absent']

requirements:
    - "python >= 2.7"
    - "cloudistics >= 0.0.1"
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
      template_name: World Community Grid
      category_name: Default
      data_center_name: DC2
      migration_zone_name: MZ1
      flash_pool_name: SP1
      nics:
        - name: 'vNIC 0'
          vnet_name: Vnet1
          type: 'Virtual Networking'
          firewall_name: 'allow all'
      tag_names:
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
      template_name: "{{ item.template_name }}"
      category_name: "{{ item.category_name }}"
      data_center_name: "{{ item.data_center_name }}"
      migration_zone_name: "{{ item.migration_zone_name }}"
      flash_pool_name: "{{ item.flash_pool_name }}"
      tag_names: "{{ item.tag_names }}"
      wait: "{{ item.wait }}"
    with_items:
      - name: xx1
        description: xx
        vcpus: 1
        memory: 1073741824
        template_name: World Community Grid
        category_name: Default
        data_center_name: DC2
        migration_zone_name: MZ1
        flash_pool_name: SP1
        nics:
          - name: 'vNIC 0'
            vnet_name: Vnet1
            type: 'Virtual Networking'
            firewall_name: 'allow all'
        tag_names:
          - TT1
          - TT2
        wait: True
      - name: xx2
        description: xx
        vcpus: 1
        memory: 1073741824
        template_name: World Community Grid
        category_name: Default
        data_center_name: DC2
        migration_zone_name: MZ1
        flash_pool_name: SP1
        nics:
          - name: 'vNIC 0'
            vnet_name: Vnet1
            type: 'Virtual Networking'
            firewall_name: 'allow all'
        tag_names:
          - TT1
          - TT2
        wait: True
      - name: xx3
        description: xx
        vcpus: 1
        memory: 1073741824
        template_name: World Community Grid
        category_name: Default
        data_center_name: DC2
        migration_zone_name: MZ1
        flash_pool_name: SP1
        nics:
          - name: 'vNIC 0'
            vnet_name: Vnet1
            type: 'Virtual Networking'
            firewall_name: 'allow all'
        tag_names:
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
from ansible.module_utils.cloudistics import cloudistics_full_argument_spec
from ansible.module_utils.cloudistics import cloudistics_lookup_by_name
from ansible.module_utils.cloudistics import cloudistics_wait_for_action

STATES = ['present', 'absent']
CPU_SIZES = [1, 2, 4, 8, 16, 32, 56]
MEMORY_SIZES = [1024, 2048, 4096, 6144, 8192, 12288, 16384, 32768, 49152, 65536, 131072, 247808]


def _nic_as_tuple(nic):
    """Formats nic as a 4-tuple, in the order specified by the Cloudistics API"""
    # N.B. string manipulations on protocols below (str(), upper()) is to
    # ensure format matches output from ELB API
    nic_list = [
        str(nic['name']),
        str(nic['type']),
    ]

    # If Virtual Networking, vnet is required, fw name is optional.
    if nic['type'] in ['Virtual Networking']:
        nic_list.append(str(nic['vnet_name']))
        nic_list.append(str(nic['firewall_name']))

    return tuple(nic_list)


def main():
    argument_spec = cloudistics_full_argument_spec(
        state=dict(required='present', choices=STATES),
        description=dict(),
        vcpus=dict(aliases=['cpus', 'vcpu', 'cpu']),
        memory=dict(),
        template_name=dict(),
        category_name=dict(),
        data_center_name=dict(),
        migration_zone_name=dict(),
        flash_pool_name=dict(),
        nics=dict(default=None, type='list'),
        tag_names=dict(type='list'),
    )

    a_module = AnsibleModule(
        argument_spec=argument_spec,

        # mutually_exclusive=(
        #     ['template_name', 'template_uuid'],
        # ),

        required_if=(
            [
                ['state', 'absent', ['name']],
                ['state', 'present', ['name', 'template_name', 'category_name', 'data_center_name',
                                      'migration_zone_name', 'flash_pool_name', 'nics']],
            ]
        ),

        # required_together=(
        #     ['a', 'b', 'b'],
        # ),

        supports_check_mode=True
    )

    name = a_module.params['name']
    state = a_module.params['state']
    wait = a_module.params['wait']
    wait_timeout = a_module.params['wait_timeout']

    changed = False
    completed = False
    status = None

    if not HAS_CL:
        a_module.fail_json(msg='Cloudistics python library required for this module')

    try:
        act_mgr = ActionsManager(cloudistics.client())
        app_mgr = ApplicationsManager(cloudistics.client())
        instance = cloudistics_lookup_by_name(app_mgr, name)

        if a_module.check_mode:
            if state == 'absent':
                a_module.exit_json(instance=instance, changed=(instance is not None))
            elif state == 'present':
                a_module.exit_json(instance=instance, changed=(instance is None))

        if state == 'absent' and instance:
            res_action = app_mgr.delete_instance(instance['uuid'])
            if res_action:
                changed = True
                if wait:
                    (completed, status) = cloudistics_wait_for_action(act_mgr, wait_timeout, res_action)
                instance = cloudistics_lookup_by_name(app_mgr, name)

        elif state == 'present' and not instance:
            # nics = [_nic_as_tuple(l) for l in a_module.params['nics']]
            nics = a_module.params['nics']

            res_action = app_mgr.create_instance(
                name=a_module.params.get('name'),
                description=a_module.params.get('description'),
                vcpus=a_module.params.get('vcpus'),
                memory=a_module.params.get('memory'),
                template_name=a_module.params.get('template_name'),
                category_name=a_module.params.get('category_name'),
                data_center_name=a_module.params.get('data_center_name'),
                migration_zone_name=a_module.params.get('migration_zone_name'),
                flash_pool_name=a_module.params.get('flash_pool_name'),
                nics=nics,
            )
            if res_action:
                changed = True
                if wait:
                    (completed, status) = cloudistics_wait_for_action(act_mgr, wait_timeout, res_action)
                instance = app_mgr.get_instance(res_action['objectUuid'])
                # instance = cloudistics_lookup_by_name(app_mgr, name)

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
