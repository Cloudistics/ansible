# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2017 Cloudistics, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


def cloudistics_full_argument_spec(**kwargs):
    spec = dict(
        name=dict(),
        wait=dict(default=True, type='bool'),
        wait_timeout=dict(default=180, type='int'),
    )
    spec.update(kwargs)
    return spec


def cloudistics_lookup_by_name(manager, given_name):
    # Search by the name given
    instances = manager.list_instances()
    try:
        return next(x for x in instances if x['name'] == given_name)
    except StopIteration:
        return None


def cloudistics_module_kwargs(**kwargs):
    ret = {}
    for key in ('mutually_exclusive', 'required_together', 'required_one_of'):
        if key in kwargs:
            if key in ret:
                ret[key].extend(kwargs[key])
            else:
                ret[key] = kwargs[key]

    return ret


def cloudistics_wait_for_action(manager, wait_time, action):
    status = None
    completed = False

    try:
        ret_action = manager.wait_for_done(action['actionUuid'], wait_time, 2)
        status = ret_action['status']

        if status == 'Completed':
            completed = True
        elif status == 'Failed':
            completed = True
        else:
            completed = False
    except:
        pass
        # raise

    return completed, status


def cloudistics_wait_for_running(manager, wait_time, uuid):
    status = None
    completed = False
    app = None

    try:
        app = manager.wait_for_running(uuid, wait_time, 2)
        status = app['status']

        if status == 'Running':
            completed = True
        else:
            completed = False
    except:
        pass

    return completed, status, app
