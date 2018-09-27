## Setup

### Get the source and set it up correctly
```shell
$ git clone git@github.com:<your repo location>/ansible.git --recursive
$ cd ansible
$ git remote add upstream https://github.com/ansible/ansible
```

### Setup your virtual env and activate it
```shell
$ source hacking/env-setup
$ pip install -r ./requirements.txt
```

## Testing

### Hacking around (against a live system)

##### Setup ENV (ThinkAgile CP)
```shell
$ export CLDSTCS_ENDPOINT_HOST=manage.cloudistics.com 
$ export CLDSTCS_API_KEY=<key>
````

##### Setup ENV (Demo)
```shell
$ export CLDSTCS_ENDPOINT_HOST=virtual-lab.cloudistics.com 
$ export CLDSTCS_API_KEY=<key>
````

##### Setup ENV (TWS)
```shell
$ export CLDSTCS_ENDPOINT_HOST=10.99.100.10
$ export CLDSTCS_VERIFY=False 
$ export CLDSTCS_API_KEY=<key>
````
##### Notes:   -c is for 'check'.  Remove when test passes for actual command.
##### Replace contents between ' ' with your ThinkAgile CP migration zone/storage pools/vdc etc where appropriate

##### List all applications (Any)
```shell
hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app_facts.py -c
````

##### Create two applications (Demo)
```shell
$ hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app.py \
    -a "count=2 name='Ansible_Test' state=present template='Centos 7.2 (64-bit)' \ 
        dc='Prod VDC' mz='Prod-MZ' fp='Prod-Storage-Pool' mem='2g' \
        vnic_name='vNIC 0' vnic_type='VNET' vnic_network='Vnet1'"\
    -c
````

##### Create two applications (SE Stack)
```shell
hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app.py \
    -a "count=2 name='Ansible_Test' state=present template='Centos 7.4 (64-bit)' \ 
        dc='Cavanaugh' mz='Reston Data Center' fp='SE Pool' mem='2g' \
        vnic_name='vNIC 0' vnic_type='VLAN' vnic_network='Default VLAN for location Primary Sales Engineering'"\
    -c
````

##### Create two applications (TWS)
```shell
$ hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app.py \
    -a "count=2 name='Ansible_Test' state=present template='Centos 7.4 template' \ 
        dc='TWS Dev Lab DC' mz='TWS Perf MZ' fp='TWS Dev Storage Pool' mem='2g' vnic_name='vNIC 0'" \
    -c
````

##### Delete two applications (All)
```shell
$ hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app.py -a "name='Ansible_Test' count=2 state=absent" -c
````

##### Start an application
```shell
$ hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app_action.py -a "name='Ansible_Test' action=start"
```

##### Stop an application
```shell
$ hacking/test-module -m lib/ansible/modules/cloud/cloudistics/cl_app_action.py -a "name='Ansible_Test' action=stop"
```

### All Tests (With Docker)
* `ansible-test sanity --docker --python 2.7 cl_app`
* Note pylint-ansible-test fails on tests from aws might want to `--skip-test pylint-ansible-test`

### All Tests (Without Docker -- DOES NOT WORK ON MAC)
* `ansible-test sanity --python 2.7 cl_app`

### Compile Tests
* `ansible-test compile --python 2.7 cl_app`
* `ansible-test compile --python 2.7 cl_app_action`

### Doc Tests
* `ansible-test sanity --test ansible-doc --python 2.7 cl_app`
* `ansible-test sanity --test ansible-doc --python 2.7 cl_app_action`

### Pep8 Tests
* `ansible-test sanity --test pep8 --python 2.7 cl_app`
* `ansible-test sanity --test pep8 --python 2.7 cl_app_action`

### Integration Tests
* `ansible-test integration -v cloudistics`


