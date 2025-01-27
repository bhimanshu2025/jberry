#!/usr/bin/python3
# Author: Himanshu Bahukhandi
# Date: 6 Oct 2022
# Email: himanshu.surendra@gmail.com
# usage : python3 get_config.py --format=set --filter=system --f list1.yml
# for filter usage refer https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/topic-map/junos-pyez-program-configuration-retrieving.html

import concurrent.futures
import argparse, yaml
from utils.junosDevice import JunosDevice
from utils.utils import parse_device_data
import os

def parse_args():
    parser = argparse.ArgumentParser(description='''Get config from Junos devices in xml or text or set format. 
                                    Also saves the output in ./dumpled_files/config/<device name>.<format>''')
    parser.add_argument('--file','-f', help='A yaml formatted file to read list of devices from. Default is .list.yml', default = 'list.yml')
    parser.add_argument('--format', help='''format can be xml or set or text. Default is "text". Also note for older Junos
    format is always xml inspite of explicitly trying to specify otherwise. ''', choices=['xml', 'text', 'set'], default = 'text')
    parser.add_argument('--filter', help='config xpath filter. eg: system/services. Default is print from root hierarchy', default = None)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    conf_xpath = args.filter
    form = args.format
    device_list_file = JunosDevice.device_list_file = args.file
    try:
        with open(device_list_file, 'r') as f:
            data = yaml.safe_load(f)
            JunosDevice.dump_path = data.get('dump_path') or os.path.dirname(os.path.realpath(__file__))
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = []
                for device in data['devices'].keys():
                    name, ip, console, user, password = parse_device_data(data, device)
                    JD = JunosDevice(name, user, password, ip, console)
                    results.append(executor.submit(JD.get_config, form, conf_xpath))
                for fu in concurrent.futures.as_completed(results):
                    fu.result()
    except FileNotFoundError as err:
        print("File not found. {}".format(err))
    except Exception as err:
        print("Could not complete operation. {}".format(err))



if __name__ == "__main__":
    main()
