#!/usr/bin/python3
# Author: Himanshu Bahukhandi
# Date: 3 Mar 2022
# Email: himanshu.surendra@gmail.com
# usage : python3 set_config.py . Can be used to push config on junos device in two ways. 
# 1. Template: Looks for config file inside files/templates/*.j2 and device specific environment variable
# files inside files/environment_variables/<device name>.yml . The device name is extracted from list.yml. If a device specific
# env file is absent, it defaults to files/environment_variables/common.yml for that device
# The script is idempotent. It also saves the delta in ./dumpled_files/delta_config/<device name>.<format>
# 2. push config from a file: If user specifies config_file_dir variable when executing the script,
# this option is selected. The config_file_dir is searched for device config to be pushed. The search is based on device 
# name specified in list.yml

import yaml, argparse
from utils.junosDevice import JunosDevice
from utils.j_email import Email
from utils.path import create_path
import os
from utils.utils import parse_device_data
import concurrent.futures
from os.path import exists

failed_results = []
from_email = ""
to_email = ""

def parse_args():
    parser = argparse.ArgumentParser(description='''Configure the j2 templated config on junos device. Looks for config file 
    inside files/templates/*.j2 defined in list.yml and device specific environment variables
    files inside files/environment_variables/<device name>.yml . the device name is extracted from list.yml and must match
    if a device specific env file is absent, it defaults to files/environment_variables/common.yml for that device.
    It also saves the diff output in ./dumpled_files/delta_config/<device name>.<format>''')
    parser.add_argument('--file','-f', help='A yaml formatted file to read list of devices from. Default is .list.yml', default = 'list.yml')
    parser.add_argument('--format', help='format can be xml or set or text. Default is "text"', choices=['xml', 'text', 'set'], default = 'text')
    parser.add_argument('--dry', '-d', type=int, help='''if set to 1,  "ONLY" prints the config diff. Default is 1.
                        Explicitly specify this argument with value 0 to commit config''', choices=[0,1], default = 1)
    parser.add_argument('--config_file_dir', help='''Complete path of directory that contails all the device specific configs per file.
                        If specified, searches for <device name>_config inside the config file directory 
                        instead of using j2 template from list.yml''', default=None)
    parser.add_argument('--overwrite', '-o', help='Whether to delete current config and overwrite new or not', choices=['True', 'False'], default = 'True')
    args = parser.parse_args()
    return args

def get_env_file(name):
    if exists('files/environment_variables/' + name + '.yml'):
        return ('files/environment_variables/' + name + '.yml') 
    else:
        return 'files/environment_variables/common.yml'

def main():
    args = parse_args()
    form = args.format
    device_list_file = JunosDevice.device_list_file = args.file
    dry = args.dry
    overwrite = args.overwrite
    config_file_dir = args.config_file_dir
    global from_email
    global to_email
    if overwrite == "True":
        overwrite = bool(1)
    else:
        overwrite = bool(0)
    try:
        with open(device_list_file, 'r') as f:
            data = yaml.safe_load(f)
            JunosDevice.dump_path = data.get('dump_path') or os.path.dirname(os.path.realpath(__file__))
            template_path=data.get('config')
            from_email = data.get('from_email')
            to_email = data.get('to_email')
            smtp_server = data.get('smtp_server')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = []
                for device in data['devices'].keys():
                    name, ip, console, user, password = parse_device_data(data, device)
                    env_file = get_env_file(name)
                    JD = JunosDevice(name, user, password, ip, console)
                    results.append(executor.submit(JD.set_config, env_file, config_file_dir, template_path, dry, form, overwrite))
                for fu in concurrent.futures.as_completed(results):
                    ret, dev_name, file_name = fu.result()
                    eval_results(ret, dev_name, file_name)
    except FileNotFoundError as err:
        print("File not found. {}".format(err))
    if len(failed_results) > 0:
        print("Emailing results")
        email_results(smtp_server)

def email_results(smtp_server=None):
    if from_email and to_email and smtp_server:
        body = "Diff detected for: "
        attachments = []
        for result in failed_results:
            body = body + result[0] + "    "
            attachments.append(result[1])
        e = Email(smtp_server)
        e.send_mail(from_email, to_email, 'jberry diff results', body, attachments)
    else:
        print("Email notifications not configured")

def eval_results(ret, dev_name, file_name):
    if ret == 1:
        print(f"Diff not None for device {dev_name}")
        failed_results.append([dev_name, file_name])
    elif ret == 0:
        print(f"Diff None for device {dev_name}")  
    else:
        print(f"Errored for device {dev_name}")   

if __name__ == "__main__":
    main()
