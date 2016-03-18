# vcenter ansible scripts

## inventory

Dynamic inventory scripts for ansible and vcenter

Based on:

* [vmware/pyvmomi-community-samples][1]
* [vmware/pyvmomi api documentation][2]
* [ansible-vmware][3] inventory script based on old pyshphere package

### dependiences

```bash
sudo dnf install python-pyvmomi PyYAML
```

### usage

* Copy vcenter_inv.yml.dist to vcenter_inv.yml and edit hostname, user,
  password. Or you can use one yaml config file with variables for
  [ansible vsphere_guest module][4] and vcenter_inv.py (just create symlink to
  group_vars/all, for example).
* Run ```./vcenter_inv.py --list```:

Example output:

```json
{
    "vcenter": {
        "children": [
            "centos64Guest",
            "sles11_64Guest"
        ]
    },
    "sles11_64Guest": {
        "hosts": [
            "192.168.1.13",
        ]
    },
    "centos64Guest": {
        "hosts": [
            "192.168.1.14",
            "192.168.1.15"
        ]
    }
}
```

* Run ansible ping with '-i' options:

```
ansible -i path/to/vcenter_inv.py -m ping
```

or add to ansible.cfg:

```ini
[defaults]
inventory = path/to/inventory/vcenter_inv.py
```

[1]: https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/list_vmwaretools_status.pyA
[2]: https://github.com/vmware/pyvmomi/tree/master/docs/vim/vm
[3]: https://github.com/RaymiiOrg/ansible-vmware
[4]: http://docs.ansible.com/ansible/vsphere_guest_module.html
