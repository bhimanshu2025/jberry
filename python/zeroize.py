#!/usr/bin/python3
# Author: Himanshu Bahukhandi
# Date: 3 Mar 2022
# Email: himanshu.surendra@gmail.com
# usage : python3 zeroize.p --f list1.yml -d 1

import yaml
import argparse
import concurrent.futures
from utils.junosDevice import JunosDevice
from utils.utils import parse_device_data

def parse_args():
    parser = argparse.ArgumentParser(description="Zeroize junos devices reading from list.yml.")
    parser.add_argument('--file','-f', help='A yaml formatted file to read list of devices from. Default is .list.yml', default = 'list.yml')
    parser.add_argument('--dry', '-d', type=int, help='''if set to 1,  "ONLY" prints list of devices that will be zeroized. 
                        Default is 1.
                        Explicitly specify this argument with value 0 to zeroize''', choices=[0,1], default = 1)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    dry = args.dry
    device_list_file = JunosDevice.device_list_file = args.file

    try:
        with open(device_list_file, 'r') as f:
            data = yaml.safe_load(f)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = []
                for device in data['devices'].keys():
                    name, ip, console, user, password = parse_device_data(data, device)
                    JD = JunosDevice(name, user, password, ip, console)
                    results.append(executor.submit(JD.zeroize_junos, dry))
                for fu in concurrent.futures.as_completed(results):
                    fu.result()
    except FileNotFoundError as err:
        print("File not found. {}".format(err))


if __name__ == "__main__":
    main()
