# INSTALLATION STEPS

## On a centos 7.5 vm
```
yum install -y python3 git
pip3 install --upgrade pip==21.0
pip3 install junos-eznc
git clone https://github.com/bhimanshu2025/jberry.git
```

## On a Ubuntu 18.04.4 vm or server
```
apt-get update
apt-get -y install python3
apt-get -y install python3-pip
apt-get -y install python3-venv
apt-get -y install git
cd /root/
python3 -m venv venv
source venv/bin/activate
git clone https://github.com/bhimanshu2025/jberry.git
pip install --upgrade pip
pip install -r jberry/python/requirements.txt
```

list.yml is the inventory file containing list of devices and their access credentials along with some optional parameters. 
The scripts can access devices over their IP, DNS name or console port. If the device name has a colon 
in its name eg: "xx:xx", its asumed that the connection needs to be over console (using netconf) else its over netconf ssh using default tcp 830 port for netconf. All devices are expected to have netconf ssh enabled. Refer jberry/python/sample.yml for all possible 
options to list inventory

There are bunch of scripts written that act as a wrapper and leverage jberry/python/utils/junosDevice module. A user can write their 
own wrapper scripts and make use of junosDevice module to achieve their end goal. These sample scripts are provided to achieve specific 
tasks as listed below under "Script Definitions" section.

Some of the tasks like set_config are capable of sending emails if a a diff is detected between the current config and some old backup
config that is passed to the script.

Run each script with -h to display all available flags

>[!NOTE]
>All logging happens locally in jberry/python/jberry.log

`python3 <script name> -h `

Example:



```
# cd /root/jberry/python/
# python3 power.py -h
usage: power.py [-h] [--power POWER] [--time TIME] [--file FILE]

Reboot/shutdown junos devices

optional arguments:
  -h, --help            show this help message and exit
  --power POWER, -p POWER
                        Possible options are "poweroff" or "reboot". Default
                        action is reboot
  --time TIME, -t TIME  poweroff or reboot in mins
  --file FILE, -f FILE  A yaml formatted file to read list of devices from.
                        Default is .list.yml
```

QA:
All my testing has been done with SRX100, vSRX (standalone)


## Script Definitions

```
get_config.py - Get config from Junos devices in xml or text or set format. The script can be used to backup config via a cronjob.

get_facts.py - Get facts from junos devices

power.py - power cycle or power off junos devices

set_config.py - configure junos devices based on jinja2 templates or provide a config file specific to each device in inventory.
The script will also run a delta config before commiting. The delta config if detected will be emailed if configured in the inventory yml file. The script can be used to do consistency checks to monitor any config changes.

show_config.py - get specific running states information from junos devices like bgp summar and states, interface status

upgrade.py - upgrade junos devices

zeroize.py - zeroize junos devices

Note: All scripts read off list.yml file unless explicitly specified
```
