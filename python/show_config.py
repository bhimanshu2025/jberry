#!/usr/bin/python3
# Author: Himanshu Bahukhandi
# Date: 3 Mar 2022
# Email: himanshu.surendra@gmail.com
# usage : python3 show_config.py <rpc> --f list1.yml



from jnpr.junos import Device
from lxml import etree
from jnpr.junos.exception import ConnectError, ConnectAuthError, RpcError
import yaml
import argparse
import concurrent.futures
import os 

final_result = []

def parse_args():
    parser = argparse.ArgumentParser(description='''show running config states from Junos devices. Also saves the output in ./dumpled_files/
                                    show_config/<device name>.<rpc>''')
    parser.add_argument('rpc', choices=['interfaces_list', 'bgp_sessions'], help='avaiable options: interfaces_list, bgp_sessions')
    parser.add_argument('--file','-f', help='A yaml formatted file to read list of devices from. Default is list.yml', default = 'list.yml')
    args = parser.parse_args()
    return args

def get_dev_user_passord(data, device):
    if data['devices'][device] and data['devices'][device].get('user'):
        user = data['devices'][device]['user']  
    else:
        user = data['user']
    if data['devices'][device] and data['devices'][device].get('password'):
        password = data['devices'][device]['password']  
    else:
        password = data['password']
    return user, password

def dev_connection(device, user, password):
    if ":" in device:
        return Device(host=device.split(':')[0], mode='telnet', 
                port=device.split(':')[1], user=user, password=password, attempts=5, gather_facts=0)
    else:
        return Device(host=device, user=user, password=password, gather_facts=0)

def bgp_sessions(dev, device):
    bgp_data = dev.rpc.get_bgp_summary_information()
    bgp_neighbors_list = []
    bgp_neighbors = bgp_data.xpath("bgp-peer/peer-address")
    for i in bgp_neighbors:
        bgp_neighbors_list.append(i.text.replace('\n',''))
    
    bgp_sessions_list = []
    bgp_sessions = bgp_data.xpath("bgp-peer/peer-state")
    for i in bgp_sessions:
        bgp_sessions_list.append(i.text.replace('\n',''))
    print("***{}***".format(device))
    print("BGP Peer Name" + "    " + "State")
    res = []
    for i in range(len(bgp_sessions_list)):
        res.append((bgp_neighbors_list[i], bgp_sessions_list[i]))
        print("{:<16} {:<10}".format(bgp_neighbors_list[i], bgp_sessions_list[i]))
    return res

def interfaces_list(dev, device):
    interface_data = dev.rpc.get_interface_information()
    int_list = []
    interface_name_list = interface_data.xpath("physical-interface/name")
    for i in interface_name_list:
        int_list.append(i.text.replace('\n',''))

    int_admin_state_list = []
    int_admin_states = interface_data.xpath("physical-interface/admin-status")
    for i in int_admin_states:
        int_admin_state_list.append(i.text.replace('\n',''))

    int_oper_state_list = []
    int_oper_states = interface_data.xpath("physical-interface/oper-status")
    for i in int_oper_states:
        int_oper_state_list.append(i.text.replace('\n',''))    
    res = []
    print("***{}***".format(device))
    print("Interface Name" + "   " +  "Admin State" + "   " + "Operational State")
    for i in range(len(int_oper_state_list)):
        res.append((int_list[i],int_admin_state_list[i],int_oper_state_list[i]))
        print("{:<16} {:<13} {:<15}".format(int_list[i], int_admin_state_list[i], int_oper_state_list[i]))
    return res

def show_config(data, device, rpc):
    user, password = get_dev_user_passord(data, device)
    dev = dev_connection(device, user, password)
    os.makedirs(os.path.dirname('dumped_files/show_config/'), exist_ok=True)
    dev.open() 
    
    if rpc == "interfaces_list":
        res = interfaces_list(dev, device)
        final_result.append(res)
    if rpc == "bgp_sessions":
        res = bgp_sessions(dev, device)
        final_result.append(res)
    with open('dumped_files/show_config/' + device + "." + rpc, 'w') as f:
        f.write(str(res))
    dev.close()
    
def main():
    args = parse_args()
    rpc = args.rpc
    device_list_file = args.file
    result = []
    try:
        with open(device_list_file, 'r') as f:
            data = yaml.safe_load(f)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = []
                for device in data['devices'].keys():
                    results.append(executor.submit(show_config, data, device, rpc))
                for fu in concurrent.futures.as_completed(results):
                    try:
                        print(fu.result())
                    except ConnectAuthError as err:
                        print("Invalid Username or password. {}".format(err))
                    except ConnectError as err:
                        print("Could not connect to {}".format(err))
    except FileNotFoundError as err:
        print("File not found. {}".format(err))

    return final_result

if __name__ == "__main__":
    main()
