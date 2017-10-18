#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

# uuid:
#   description:
#     - UUID of the application to perform action option
#   required: false
#   default: true
DOCUMENTATION = '''
---
module: cl_app_action
short_description: Perform actions on Applications from Cloudistics
extends_documentation_fragment: cloudistics
version_added: "2.4"
author: "Joe Cavanaugh (@juniorfoo)"
description:
   - Perform application actions on an existing applicatios from Cloudistics.
     This module does not return any data other than changed true/false and
     completed true/false
options:
  action:
    description:
      - Perform the given action.
    required: true
    choices: [stop, start, restart, pause, resume]

requirements:
    - "python >= 2.7"
    - "cloudistics >= 0.0.1"
'''

EXAMPLES = '''
# Suspend an application
- cl_app_action:
      action: pause
      name: test_name
      wait: True
      wait_timeout: 300
'''

try:
    import cloudistics
    from cloudistics import ActionsManager, ApplicationsManager, exceptions

    HAS_CL = True
except ImportError as e:
    HAS_CL = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudistics import cloudistics_full_argument_spec
from ansible.module_utils.cloudistics import cloudistics_lookup_by_name
from ansible.module_utils.cloudistics import cloudistics_wait_for_action
from ansible.module_utils.cloudistics import cloudistics_wait_for_running

# TODO: get this info from API
ACTIONS = ['stop', 'start', 'restart', 'pause', 'resume']

_action_map = {'stop': 'Shut down',
               'start': 'Running',
               'restart': 'Restarting',
               'pause': 'Paused',
               'resume': 'Running',
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

        required_if=(
            [
                ['action', 'pause', ['name']],
                ['action', 'restart', ['name']],
                ['action', 'resume', ['name']],
                ['action', 'start', ['name']],
                ['action', 'stop', ['name']],
            ]
        ),

        # required_together=(
        #     ['a', 'b', 'b'],
        # ),
        supports_check_mode=True
    )

    name = a_module.params['name']
    action = a_module.params['action']
    wait = a_module.params['wait']
    wait_timeout = a_module.params['wait_timeout']

    changed = True
    completed = False
    status = None
    res_action = None
    running = None

    if not HAS_CL:
        a_module.fail_json(msg='Cloudistics python library required for this module')

    try:
        act_mgr = ActionsManager(cloudistics.client())
        app_mgr = ApplicationsManager(cloudistics.client())
        instance = cloudistics_lookup_by_name(app_mgr, name)

        if not instance:
            a_module.fail_json(msg='Could not find application %s' % name)

        if a_module.check_mode:
            a_module.exit_json(changed=_application_status_change(action, instance))

        if not _application_status_change(action, instance):
            a_module.exit_json(changed=False)

        #
        # Do the actions requested and just set our variables, return will happen later
        #
        instance_id = instance['uuid']

        if action == 'pause':
            res_action = app_mgr.suspend_instance(instance_id)
        elif action == 'restart':
            res_action = app_mgr.restart_instance(instance_id)
        elif action == 'resume':
            res_action = app_mgr.resume_instance(instance_id)
        elif action == 'start':
            res_action = app_mgr.start_instance(instance_id)
        elif action == 'stop':
            res_action = app_mgr.stop_instance(instance_id)

        if res_action and wait:
            (completed, status) = cloudistics_wait_for_action(act_mgr, wait_timeout, res_action)
            if completed and action in ['restart', 'resume', 'start']:
                (completed, running, app) = cloudistics_wait_for_running(app_mgr, wait_timeout, instance_id)

        # Get an updated version of the instance
        instance = app_mgr.get_instance(instance['uuid'])

        # a_module.exit_json(changed=changed, completed=completed, status=status,
        #                    res_action=res_action, wait=wait)
        a_module.exit_json(changed=changed, completed=completed, status=status, instance=instance)

    except exceptions.CloudisticsAPIError as e:
        a_module.fail_json(msg=e.message)


if __name__ == '__main__':
    main()
