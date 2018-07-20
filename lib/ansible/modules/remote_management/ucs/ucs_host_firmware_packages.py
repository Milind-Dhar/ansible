#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ucs_host_firmware_packages
short_description: Configures firmware on Cisco UCS. 
description:
- Configures fimware on Cisco UCS 
- Configures firmware on Cisco UCS 
options:
  blade_bundle_version:
    description:
    - Configures the firmware version for blade server.
    default:
    required: yes
  rack_bundle_version:
    description:
    - Configures the firmware version for rack server.
    default:
    required: yes
  exclude_server_components:
    description:
    - List of excluded server components
    default: [ "local-disk", "adaptor" ]
    choices: [ "local-disk", "adaptor","TBD" ]
    required: no
  descr:
    description:
    - Description for the host firmware package
    default:
    required: yes
  name:
    description:
    - Name for the host firmware package
    default:
    required: yes
  state:
    description:
    - If present, will verify the host firmware package is present and will create if needed.
    - If absent, will verify the host firmware package is absent and will delete if needed.
    choices: [present, absent]
    default: present
requirements:
- ucsmsdk
author:
- Milind Dhar (midhar@cisco.com)
- CiscoUcs (@CiscoUcs)
version_added: '2.8'
'''

EXAMPLES = '''
- name: Test ucs_host_firmware_packages module  
  ucs_host_firmware_packages:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: MyHostFirmWarePackage
    descr: 'some description'
    rack_bundle_version: "3.1(2c)C"
    exclude_server_components:
      - "local-disk"
      - "adaptor"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec

def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        descr=dict(type='str', required=False),
        blade_bundle_version=dict(type='str', required=False),
        rack_bundle_version=dict(type='str', required=False),
        exclude_server_components=dict(type='list', required=False),
    )
    
    module = AnsibleModule(argument_spec,)
    ucs = UCSModule(module)
    err = False
    print("********Inputs start********");
    print("name=",module.params['name']);
    print("state=",module.params['state']);
    print("descr=",module.params['descr']);
    print("blade_bundle_version=",module.params['blade_bundle_version']);
    print("rack_bundle_version=",module.params['rack_bundle_version']);
    print("exclude_server_components=",module.params['exclude_server_components']);
    print("********Inputs end********");

    # UCSModule creation above verifies ucsmsdk is present and exits on failure, so additional imports are done below.
    from ucsmsdk.mometa.firmware.FirmwareComputeHostPack import FirmwareComputeHostPack
    from ucsmsdk.mometa.firmware.FirmwareExcludeServerComponent import FirmwareExcludeServerComponent
    changed = False
    try:
        mo_exists = False
        props_match = False
        # dn is org-root/fw-host-pack-<name>
        #dn_base = 'org-root/fw-host-pack-'
        dn_base = 'org-root'
        dn = dn_base+'/fw-host-pack-'+module.params['name'] 
        mo = ucs.login_handle.query_dn(dn)
        if mo:
            mo_exists = True
        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if mo_exists:
                if not module.check_mode:
                    ucs.login_handle.remove_mo(mo)
                    ucs.login_handle.commit()
                changed = True
        else:
            if mo_exists:
                print("mo exists")
                # check top-level mo props 
                kwargs = dict(name=module.params['name'])
                kwargs = dict(descr=module.params['descr'])
                kwargs = dict(descr=module.params['blade_bundle_version'])
                kwargs = dict(descr=module.params['rack_bundle_version'])
                if (mo.check_prop_match(**kwargs)):
                    props_match = True
            if not props_match:
                print("mo do not exists or props do not match")
                mo = FirmwareComputeHostPack(
                        parent_mo_or_dn=dn_base,
                        name=module.params['name'],
                        descr=module.params['descr'],
                        blade_bundle_version=module.params['blade_bundle_version'],
                        rack_bundle_version=module.params['rack_bundle_version'],
                )
                ucs.login_handle.add_mo(mo, True)
                ucs.login_handle.commit()
                changed = True
            if  module.params['exclude_server_components'] is None:
              module.params['exclude_server_components'] = []
            for server_comp in module.params['exclude_server_components']:
                print("server_comp=",server_comp)
                mo_exclude_component_exists=False
                print(dn+'/exclude-server-component-'+server_comp)
                mo_exclude_component = ucs.login_handle.query_dn(dn+'/exclude-server-component-'+server_comp)
                if mo_exclude_component: 
                    mo_exclude_component_exists=True
                print("mo_exclude_component_exists=",mo_exclude_component_exists) 
                if not mo_exclude_component_exists:
                    mo_exclude_component = FirmwareExcludeServerComponent(
                        parent_mo_or_dn=dn,
                        server_component=server_comp,
                    )
                    ucs.login_handle.add_mo(mo_exclude_component, True)
                    ucs.login_handle.commit()
                    changed = True
            mo_list = ucs.login_handle.query_children(in_mo=mo, class_id="FirmwareExcludeServerComponent")
            for child in mo_list:
                #print(str(child))
                #print(child.server_component)
                if child.server_component not in module.params['exclude_server_components']:
                    print(child.server_component,"to be removed");
                    ucs.login_handle.remove_mo(child)
                    ucs.login_handle.commit()
                
        print("props_match=",props_match);
        #print(str(mo));
                

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed

    if err:
        module.fail_json(**ucs.result)

    module.exit_json(**ucs.result)



if __name__ == '__main__':
    main()
