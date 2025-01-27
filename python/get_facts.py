#!/usr/bin/python3
# Author: Himanshu Bahukhandi
# Date: 6 Oct 2022
# Email: himanshu.surendra@gmail.com
# usage : python3 get_facts.py -k serialnumber -f list1.yml
# files inside files/environment_variables/<device name>.yml . the device name is extracted from list.yml

import concurrent.futures
import argparse, yaml
from utils.junosDevice import JunosDevice
import os
from utils.utils import parse_device_data

def parse_args():
    parser = argparse.ArgumentParser(description="Get facts from junos devices. Saves output in a file under ./dumped_files/facts/<device_name>_facts")
    parser.add_argument('--file','-f', help='A yaml formatted file to read list of devices from. Default is .list.yml', default = 'list.yml')
    parser.add_argument('--key','-k', help='find a specific fact value. eg: serialnumber or version', default = None)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    key = args.key
    device_list_file = JunosDevice.device_list_file = args.file
    try:
        with open(device_list_file, 'r') as f:
            data = yaml.safe_load(f)
            JunosDevice.dump_path = data.get('dump_path')  or os.path.dirname(os.path.realpath(__file__))
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = []
                for device in data['devices'].keys():
                    name, ip, console, user, password = parse_device_data(data, device)
                    JD = JunosDevice(name, user, password, ip, console)
                    results.append(executor.submit(JD.get_facts, key))
                for fu in concurrent.futures.as_completed(results):
                    fu.result()
    except FileNotFoundError as err:
        print("File not found. {}".format(err))

if __name__ == "__main__":
    main()
