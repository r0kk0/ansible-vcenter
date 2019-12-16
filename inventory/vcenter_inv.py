#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Ansible inventory script for VMWare vCenter
'''

import argparse
import atexit
import json
import os
from collections import Counter
from getpass import getpass

import requests
import yaml
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim


_DEFAULT_GROUP = 'ungrouped'


# disable  urllib3 warnings
if hasattr(requests.packages.urllib3, 'disable_warnings'):
    requests.packages.urllib3.disable_warnings()


def parse_args():
    '''Parse arguments'''
    parser = argparse.ArgumentParser(description='Get list of running VMs from vcenter')
    parser.add_argument('--list', action='store_true',
                        help='List all running VMs with root group "vcenter"')
    parser.add_argument('--host',
                        help='Return some guest information')
    args = parser.parse_args()
    if not args.list and not args.host:
        parser.print_help()
        parser.exit()

    return args


def load_config(path):
    '''Load config file'''
    if not os.path.exists(path):
        print("Configuration file not found: %s" % path)
        exit(1)

    with open(path, 'r') as f:
        try:
            content = yaml.load(f, Loader=yaml.SafeLoader)
        except yaml.YAMLError as error:
            print(error)
            exit(1)

    return content['vcenter']


def get_vms(content):
    '''Get list of vms objects'''
    obj_view = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True)
    vms_list = obj_view.view
    obj_view.Destroy()

    return vms_list


def extract_domain(hostname):
    '''Extracts domain name from `hostname` (str). Replaces bad ansible group charaters with '_'.

    >>> extract_domain('hostname')
    >>> extract_domain('example.com')
    'com'
    >>> extract_domain('hostname.example.com')
    'example_com'
    >>> extract_domain('hostname.t0.example.com')
    't0_example_com'
    '''

    if '.' not in hostname:
        return

    items = hostname.split('.')
    return '_'.join(items[1:])


def create_inventory_list(vm_list, group_by='guestId', use_ip=False):
    '''
    Arguments:
        group_by (str): guestId, domain - group hosts by guestId or domain
        use_ip (bool): use ip addresses instead of hostnames
    '''

    inventory = {}
    inventory['vcenter'] = {}
    inventory['vcenter']['children'] = []

    for vm in vm_list:
        if vm.guest.guestState == 'notRunning':
            continue

        if vm.guest.toolsStatus == 'toolsNotInstalled':
            continue

        hostname = vm.guest.hostName

        group = vm.guest.guestId or vm.guest.guestFamily or _DEFAULT_GROUP
        if group_by == 'domain':
            group = extract_domain(hostname) or _DEFAULT_GROUP
        if group not in inventory['vcenter']['children']:
            inventory['vcenter']['children'].append(group)

        if group not in inventory:
            inventory[group] = {}
            inventory[group]['hosts'] = []

        value = vm.guest.ipAddress if use_ip else hostname
        inventory[group]['hosts'].append(value)

    return json.dumps(inventory, indent=2)


def create_host_info(vm_list, host):
    '''Create host information json object for ansible'''
    vm_info = {}
    for vm in vm_list:
        ipaddress = vm.guest.ipAddress
        hostname = vm.guest.hostName
        if host in [ipaddress, hostname]:
            vm_info['vm_name'] = vm.name
            vm_info['vm_guest_fullname'] = vm.guest.guestFullName
            vm_info['vm_guest_toolsStatus'] = vm.guest.toolsStatus
            vm_info['vm_guest_toolsRunningStatus'] = vm.guest.toolsRunningStatus
            vm_info['vm_guest_guestId'] = vm.guest.guestId
            vm_info['vm_guest_hostName'] = vm.guest.hostName

    return json.dumps(vm_info, indent=4)


def main():
    '''Main program'''
    args = parse_args()

    default_cfg = '%s/%s.yml' % (os.path.dirname(os.path.abspath(__file__)),
                                 os.path.splitext(os.path.basename(__file__))[0])
    cfg_file = os.getenv('VCENTER_INV_CFG', default=default_cfg)
    config = load_config(cfg_file)

    env_pwd = os.getenv('VCENTER_INV_PWD')
    password = config['password'] or env_pwd or getpass(prompt="enter password: ")
    # connect to vc
    si = SmartConnectNoSSL(
        host=config['host'],
        user=config['username'],
        pwd=password,
        port=int(config['port']),
    )
    # disconnect vc
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()

    vm_list = get_vms(content)
    if args.list:
        result = create_inventory_list(
            vm_list, group_by=config['group_by'], use_ip=config['use_ip'])
    elif args.host:
        result = create_host_info(vm_list, host=args.host)
    print(result)


if __name__ == "__main__":
    main()
