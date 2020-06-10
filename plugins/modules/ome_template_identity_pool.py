#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0.12
# Copyright (C) 2020 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ome_template_identity_pool
short_description: Attach or detach an identity pool to a requested template on OpenManage Enterprise.
version_added: "2.9"
description: This module allows to-
  - Attach an identity pool to a requested template on OpenManage Enterprise.
  - Detach an identity pool from a requested template on OpenManage Enterprise.
options:
  hostname:
    description: Target IP Address or hostname.
    type: str
    required: true
  username:
    description: Target username.
    type: str
    required: true
  password:
    description: Target user password.
    type: str
    required: true
  port:
    description: Target HTTPS port.
    type: int
    default: 443
  template_name:
    description: Name of the template to which an identity pool is attached or detached.
    type: str
    required: true
  identity_pool_name:
    description: Name of the identity pool.
      - To attach an identity pool to a template, provide the name of the identity pool.
      - This option is not applicable when detaching an identity pool from a template.
    type: str
requirements:
    - "python >= 2.7.5"
author: "Felix Stephen (@felixs88)"
'''

EXAMPLES = r'''
---
- name: Attach an identity pool to a template.
  ome_template_identity_pool:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    template_name: template_name
    identity_pool_name: identity_pool_name

- name: Detach an identity pool from a template.
  ome_template_identity_pool:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    template_name: template_name
'''

RETURN = r'''
---
msg:
  type: str
  description: Overall identity pool status of the attach or detach operation.
  returned: always
  sample: Successfully attached identity pool to template.
error_info:
  description: Details of the HTTP Error.
  returned: on HTTP error
  type: dict
  sample: {
    "error": {
      "code": "Base.1.0.GeneralError",
      "message": "A general error has occurred. See ExtendedInfo for more information.",
      "@Message.ExtendedInfo": [
        {
          "MessageId": "GEN1234",
          "RelatedProperties": [],
          "Message": "Unable to process the request because an error occurred.",
          "MessageArgs": [],
          "Severity": "Critical",
          "Resolution": "Retry the operation. If the issue persists, contact your system administrator."
        }
      ]
    }
  }
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dellemc.openmanage.plugins.module_utils.ome import RestOME
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ssl import SSLError

CONFIG_URI = "TemplateService/Actions/TemplateService.UpdateNetworkConfig"
TEMPLATE_URI = "TemplateService/Templates"
IDENTITY_URI = "IdentityPoolService/IdentityPools"


def get_template_id(rest_obj, module):
    """Get template id based on requested template name."""
    template_name = module.params["template_name"]
    query_param = {"$filter": "Name eq '{0}'".format(template_name)}
    template_req = rest_obj.invoke_request("GET", TEMPLATE_URI, query_param=query_param)
    for each in template_req.json_data.get('value'):
        if each['Name'] == template_name:
            template_id = each['Id']
            break
    else:
        module.fail_json(msg="Unable to complete the operation because the requested template"
                             " with name '{0}' is not present.".format(template_name))
    return template_id


def get_identity_id(rest_obj, module):
    """Get identity pool id based on requested identity pool name."""
    identity_name = module.params["identity_pool_name"]
    resp = rest_obj.get_all_report_details(IDENTITY_URI)
    for each in resp["report_list"]:
        if each['Name'] == identity_name:
            identity_id = each['Id']
            break
    else:
        module.fail_json(msg="Unable to complete the operation because the requested identity"
                             " pool with name '{0}' is not present.".format(identity_name))
    return identity_id


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": "str"},
            "username": {"required": True, "type": "str"},
            "password": {"required": True, "type": "str", "no_log": True},
            "port": {"required": False, "type": "int", "default": 443},
            "template_name": {"required": True, "type": "str"},
            "identity_pool_name": {"required": False, "type": "str"},
        },
    )
    try:
        with RestOME(module.params, req_session=True) as rest_obj:
            template_id = get_template_id(rest_obj, module)
            identity_id, message = 0, "Successfully detached identity pool from template."
            if module.params["identity_pool_name"] is not None:
                identity_id = get_identity_id(rest_obj, module)
                message = "Successfully attached identity pool to template."
            payload = {"TemplateId": template_id, "IdentityPoolId": identity_id}
            resp = rest_obj.invoke_request("POST", CONFIG_URI, data=payload)
            if resp.status_code == 200:
                module.exit_json(msg=message, changed=True)
    except HTTPError as err:
        module.fail_json(msg=str(err), error_info=json.load(err))
    except URLError as err:
        module.exit_json(msg=str(err), unreachable=True)
    except (ValueError, TypeError, ConnectionError, SSLError, SSLValidationError) as err:
        module.fail_json(msg=str(err))
    except Exception as err:
        module.fail_json(msg=str(err))


if __name__ == "__main__":
    main()
