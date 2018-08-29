#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project and Cloudistics Inc.
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
  name:
    description:
      - Name of the application
    required: false
  uuid:
    description:
      - UUID of the application
    required: false
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
  vnic_type:
    description:
      - Virtual NIC Type
    required: false
    choices: ['VLAN', 'VNET']
  vnic_network:
    description:
      - Virtual NIC Network
    required: false
  vnic_fw:
    description:
      - Virtual NIC FW
    required: false
  vnic_mac:
    description:
      - Virtual NIC MAC Address
    required: false
  group:
    description:
      - Group to add the applications to.
    required: false
  disks:
    description:
      - List of disk sizes to be assigned to new application (i.e. [1tb, 10tb]).
    required: false
    default: []
  count:
    description:
      - number of instances to create/delete. If >1, the number will be appended to the name (name_1)
    required: false
    default: 1
    aliases: []
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
      vnic_type: 'VNET'
      vnic_network: Vnet1
      vnic_fw: 'allow all'
      tags:
        - TT1
        - TT2
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
      vnic_type: 'VNET'
      vnic_network: Vnet1
        vnic_fw: 'allow all'
        tags:
          - TT1
          - TT2
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
        vnic_type: 'VNET'
        vnic_network: Vnet1
        vnic_fw: 'allow all'
        tags:
          - TT1
          - TT2
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
        vnic_type: 'VNET'
        vnic_network: Vnet1
        vnic_fw: 'allow all'
        tags:
          - TT1
          - TT2

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

import logging

try:
    import cloudistics
    from cloudistics import ActionsManager
    from cloudistics import ApplicationDisksManager
    from cloudistics import ApplicationGroupsManager
    from cloudistics import ApplicationsManager
    from cloudistics import CloudisticsAPIError
    from cloudistics import exceptions

    HAS_CL = True
except ImportError:
    HAS_CL = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudistics import cloudistics_convert_memory_abbreviation_to_bytes
from ansible.module_utils.cloudistics import cloudistics_full_argument_spec
from ansible.module_utils.cloudistics import cloudistics_lookup_by_name
from ansible.module_utils.cloudistics import cloudistics_wait_for_action
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

STATES = ['absent', 'present']
TYPES = ['VLAN', 'VNET']
WAIT_TIMEOUT = 600


def build_name(name_prefix, count, index):
    if count > 1:
        return "%s_%d" % (name_prefix, (index + 1))
    else:
        return name_prefix


def create_instances(a_module, app_mgr, act_mgr, check_mode=False):
    """
    Creates new instances

    a_module : AnsibleModule object
    app_mgr : Cloudistics Applications Manager
    act_mgr : Cloudistics Actions Manager

    Returns:
        A list of dictionaries with instance information
        about the instances that were created
    """

    name_prefix = a_module.params.get('name')
    count = int(a_module.params.get('count'))
    count_remaining = count
    instance_uuid_array = []

    # Figure out if we have any instances already running with our name (so we are idempotent with respect to instances)
    list_instances = app_mgr.list()
    for x in range(count):
        name = build_name(name_prefix, count, x)
        existing_instance = cloudistics_lookup_by_name(app_mgr, name, None, list_instances)
        if existing_instance is not None:
            instance_uuid_array.append(existing_instance['uuid'])

    count_remaining = count_remaining - len(instance_uuid_array)

    changed = False
    if count_remaining > 0:
        changed = True

    create_actions = []

    if not check_mode:
        mem_in_bytes = cloudistics_convert_memory_abbreviation_to_bytes(a_module.params.get('memory'))
        for x in range(count_remaining):
            name = build_name(name_prefix, count, x)
            create_action = app_mgr.create(
                name=name,
                description=a_module.params.get('description'),
                vcpus=a_module.params.get('vcpus'),
                memory=mem_in_bytes,
                template_name_or_uuid=a_module.params.get('template'),
                cat_name_or_uuid=a_module.params.get('category'),
                dc_name_or_uuid=a_module.params.get('data_center'),
                mz_name_or_uuid=a_module.params.get('migration_zone'),
                fp_name_or_uuid=a_module.params.get('flash_pool'),
                vnic_name=a_module.params.get('vnic_name'),
                vnic_type=a_module.params.get('vnic_type'),
                vnic_network_name_or_uuid=a_module.params.get('vnic_network'),
                vnic_firewall_name_or_uuid=a_module.params.get('vnic_fw'),
                vnic_mac_address=a_module.params.get('vnic_mac_address'))
            create_actions.append(create_action)

    for action in create_actions:
        instance_uuid_array.append(action['objectUuid'])

        cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, action)

    disks_changed = ensure_disks(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode)
    group_changed = ensure_group(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode)
    vcpu_changed = ensure_vcpus(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode)
    memory_changed = ensure_memory(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode)

    instance_dict_array = []
    for uuid in instance_uuid_array:
        instance_dict_array.append(camel_dict_to_snake_dict(app_mgr.detail(uuid)))

    return instance_dict_array, instance_uuid_array, (
            changed or disks_changed or group_changed or vcpu_changed or memory_changed)


def delete_instances(a_module, app_mgr, act_mgr, check_mode=False):
    """
    Deletes existing instances

    a_module : AnsibleModule object
    app_mgr : Cloudistics Applications Manager
    act_mgr : Cloudistics Actions Manager

    Returns:
        A list of dictionaries with instance information
        about the instances that were removed
    """

    name_prefix = a_module.params.get('name')
    count = int(a_module.params.get('count'))
    instance_dict_array = []
    instance_uuid_array = []
    changed = False

    remove_actions = []
    list_instances = app_mgr.list()
    for x in range(count):
        name = build_name(name_prefix, count, x)
        existing_instance = cloudistics_lookup_by_name(app_mgr, name, None, list_instances)
        if existing_instance is not None:
            instance_dict_array.append(camel_dict_to_snake_dict(existing_instance))
            instance_uuid_array.append(existing_instance['uuid'])

            if not check_mode:
                try:
                    remove_action = app_mgr.delete(existing_instance['uuid'])
                    remove_actions.append(remove_action)
                except CloudisticsAPIError as e:
                    a_module.fail_json(
                        msg='Unable to delete instance %s, error: %s' % (existing_instance['uuid'], e))

            changed = True

    for action in remove_actions:
        cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, action)

    return instance_dict_array, instance_uuid_array, changed


def ensure_disks(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode):
    """
    Ensures the instances have the correct disks attached

    a_module : AnsibleModule object
    app_mgr : Cloudistics Applications Manager
    act_mgr : Cloudistics Actions Manager
    instance_dict_array : Instance Dictionary Array

    Returns: Flag to indicate if we changed the disks
    """

    app_disk_mgr = ApplicationDisksManager(cloudistics.client(api_key=a_module.params.get('api_key')))
    existing_disk_dict = {}
    changed = False

    for uuid in instance_uuid_array:
        instance = app_mgr.detail(uuid)
        for existing_disk in instance['disks']:
            existing_disk_dict[existing_disk['name']] = existing_disk

        disk_sizes_array = a_module.params.get('disks')
        for idx, disk_size in enumerate(disk_sizes_array):
            new_disk_name = 'Disk %d' % (idx + 1)
            new_disk_size = cloudistics_convert_memory_abbreviation_to_bytes(disk_size)
            if new_disk_name not in existing_disk_dict:
                changed = True
                if not check_mode:
                    # We need to create the disk
                    disk_add_action = app_disk_mgr.create(uuid, new_disk_name, new_disk_size)
                    cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, disk_add_action)

    return changed


def ensure_group(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode):
    """
    Ensures the instances are in the correct group

    a_module : AnsibleModule object
    app_mgr : Cloudistics Applications Manager
    act_mgr : Cloudistics Actions Manager
    instance_dict_array : Instance Dictionary Array

    Returns: Flag to indicate if we changed the disks
    """

    changed = False
    group_identifier = a_module.params.get('group')

    if group_identifier:
        app_group_mgr = ApplicationGroupsManager(cloudistics.client(api_key=a_module.params.get('api_key')))

        existing_group = cloudistics_lookup_by_name(app_group_mgr, group_identifier, None)
        if not existing_group:
            changed = True
            if check_mode:
                return changed
            else:
                # We need to create the group
                group_add_action = app_group_mgr.create(a_module.params.get('data_center'), group_identifier)
                cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, group_add_action)

        group_add_app_action = app_group_mgr.add_applications(group_identifier, instance_uuid_array)
        cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, group_add_app_action)


def ensure_memory(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode):
    """
    Ensures the instances have the correct memory

    a_module : AnsibleModule object
    app_mgr : Cloudistics Applications Manager
    act_mgr : Cloudistics Actions Manager
    instance_dict_array : Instance Dictionary Array

    Returns: Flag to indicate if we changed the memory
    """

    changed = False

    for uuid in instance_uuid_array:
        mem_in_bytes = cloudistics_convert_memory_abbreviation_to_bytes(a_module.params.get('memory'))
        instance = app_mgr.detail(uuid)
        if not instance['memory'] == mem_in_bytes:
            changed = True
            if not check_mode:
                # We need to update the memory
                change_action = app_mgr.memory(uuid, mem_in_bytes)
                cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, change_action)

    return changed


def ensure_vcpus(a_module, app_mgr, act_mgr, instance_uuid_array, check_mode):
    """
    Ensures the instances have the correct vcpus

    a_module : AnsibleModule object
    app_mgr : Cloudistics Applications Manager
    act_mgr : Cloudistics Actions Manager
    instance_dict_array : Instance Dictionary Array

    Returns: Flag to indicate if we changed the vcpus
    """

    changed = False

    for uuid in instance_uuid_array:
        instance = app_mgr.detail(uuid)
        if not instance['vcpus'] == a_module.params.get('vcpus'):
            changed = True
            if not check_mode:
                # We need to update the VCPU count
                change_action = app_mgr.vcpus(uuid, a_module.params.get('vcpus'))
                cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, change_action)

    return changed


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
        vnic_type=dict(choices=TYPES),
        vnic_network=dict(),
        vnic_fw=dict(),
        vnic_mac=dict(),
        disks=dict(type='list', default=[]),
        group=dict(),
        tags=dict(type='list'),
        count=dict(type='int', default='1'),
    )

    a_module = AnsibleModule(
        argument_spec=argument_spec,

        mutually_exclusive=(
            ['name', 'uuid'],
        ),

        required_if=(
            [
                # ['state', 'absent', ['name']],
                ['state', 'present', ['name', 'template', 'data_center', 'migration_zone', 'flash_pool', 'vnic_type',
                                      'vnic_network', 'disks', 'count']],
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

    # logger = logging.getLogger()
    # logger.addHandler(logging.StreamHandler())
    # logger.setLevel(logging.INFO)
    # logger.setLevel(logging.DEBUG)

    if not a_module.no_log:
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        if a_module._debug:
            logger.setLevel(logging.DEBUG)

    state = a_module.params['state']
    changed = False
    instance_dict_array = []
    instance_ids_array = []

    if not HAS_CL:
        a_module.fail_json(msg='Cloudistics python library (>=0.9.8) required for this module')

    try:
        act_mgr = ActionsManager(cloudistics.client(api_key=a_module.params.get('api_key')))
        app_mgr = ApplicationsManager(cloudistics.client(api_key=a_module.params.get('api_key')))

        if a_module.check_mode:
            if state == 'absent':
                (instance_dict_array, instance_ids_array, changed) = delete_instances(a_module, app_mgr, act_mgr, True)
            elif state == 'present':
                (instance_dict_array, instance_ids_array, changed) = create_instances(a_module, app_mgr, act_mgr, True)
        else:
            if state == 'absent':
                (instance_dict_array, instance_ids_array, changed) = delete_instances(a_module, app_mgr, act_mgr, False)
            elif state == 'present':
                (instance_dict_array, instance_ids_array, changed) = create_instances(a_module, app_mgr, act_mgr, False)

        a_module.exit_json(changed=changed, instance_ids=instance_ids_array, instances=instance_dict_array)
    except exceptions.CloudisticsAPIError as e:
        a_module.fail_json(msg=e.message)

    # except TypeError as e:
    #     a_module.fail_json(msg=str(e))

    except ValueError as e:
        a_module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
