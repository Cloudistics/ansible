#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project and Cloudistics Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cl_app_action
extends_documentation_fragment: cloudistics
short_description: Perform actions on Applications from Cloudistics
description:
   - Perform application actions on an existing applications from Cloudistics.
options:
  name:
    description:
      - Name of the application
    required: false
  uuid:
    description:
      - UUID of the application
    required: false
  action:
    description:
      - Perform the given action.
    required: true
    choices: [restarted, resumed, shutdown, started, stopped, suspended]
'''

EXAMPLES = '''
# Suspend an application
- cl_app_action:
      action: paused
      name: test_name
'''

import logging

try:
    import cloudistics
    from cloudistics import ActionsManager
    from cloudistics import ApplicationsManager
    from cloudistics import exceptions

    HAS_CL = True
except ImportError as e:
    HAS_CL = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudistics import cloudistics_full_argument_spec
from ansible.module_utils.cloudistics import cloudistics_wait_for_action
from ansible.module_utils.cloudistics import cloudistics_wait_for_running
from ansible.module_utils.cloudistics import cloudistics_wait_for_ip_address

ACTIONS = ['restarted', 'resumed', 'shutdown', 'started', 'stopped', 'suspended']
WAIT_TIMEOUT = 600

_action_map = {
    'restarted': 'Restarting',
    'resumed': 'Running',
    'shutdown': 'Shut down',
    'started': 'Running',
    'stopped': 'Shut down',
    'suspended': 'Paused',
}


def _application_status_change(action, instance):
    """Check if application status would change."""
    return not instance['status'] == _action_map[action]


def main():
    argument_spec = cloudistics_full_argument_spec(
        action=dict(required=True, choices=ACTIONS),
    )

    a_module = AnsibleModule(
        argument_spec=argument_spec,

        # mutually_exclusive=(
        #     ['template_name', 'template_uuid'],
        # ),

        # required_if=(
        #     [
        #         ['action', 'restarted', ['name']],
        #         ['action', 'resumed', ['name']],
        #         ['action', 'shutdown', ['name']],
        #         ['action', 'started', ['name']],
        #         ['action', 'stopped', ['name']],
        #         ['action', 'suspended', ['name']],
        #     ]
        # ),

        # required_together=(
        #     ['a', 'b', 'b'],
        # ),
        supports_check_mode=True
    )

    if not a_module.no_log:
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

        if a_module._debug:
            logger.setLevel(logging.DEBUG)

    identifier = a_module.params['name'] or a_module.params['uuid']
    action = a_module.params['action']

    changed = True
    completed = False
    status = None
    res_action = None

    if not HAS_CL:
        a_module.fail_json(msg='Cloudistics python library required for this module')

    try:
        act_mgr = ActionsManager(cloudistics.client(api_key=a_module.params.get('api_key')))
        app_mgr = ApplicationsManager(cloudistics.client(api_key=a_module.params.get('api_key')))
        instance = app_mgr.detail(identifier)

        if not instance:
            a_module.fail_json(msg='Could not find application %s' % identifier)

        if a_module.check_mode:
            a_module.exit_json(changed=_application_status_change(action, instance),
                               completed=False, status=instance['status'], instance=instance)

        if not _application_status_change(action, instance):
            a_module.exit_json(changed=False, completed=False, status=instance['status'], instance=instance)

        #
        # Do the actions requested and just set our variables, return will happen later
        #
        instance_id = instance['uuid']

        if action == 'restarted':
            res_action = app_mgr.restart(instance_id)
        elif action == 'resumed':
            res_action = app_mgr.resume(instance_id)
        elif action == 'shutdown':
            res_action = app_mgr.shutdown(instance_id)
        elif action == 'started':
            res_action = app_mgr.start(instance_id)
        elif action == 'stopped':
            res_action = app_mgr.stop(instance_id)
        elif action == 'suspended':
            res_action = app_mgr.suspend(instance_id)

        if res_action:
            (completed, status) = cloudistics_wait_for_action(act_mgr, WAIT_TIMEOUT, res_action)
            if completed and action in ['restarted', 'resumed', 'started']:
                (completed, running, app) = cloudistics_wait_for_running(app_mgr, WAIT_TIMEOUT, instance_id)

        # Get an updated version of the instance (after waiting for an IP address)
        instance, has_address = cloudistics_wait_for_ip_address(app_mgr, WAIT_TIMEOUT, instance_id)
        if has_address:
            a_module.exit_json(changed=changed, completed=completed, status=status, instance=instance)
        else:
            a_module.fail_json(msg='Instance did not have an IP assigned in time', instance=instance)

    except exceptions.CloudisticsAPIError as e:
        a_module.fail_json(msg=e.message)


if __name__ == '__main__':
    main()
