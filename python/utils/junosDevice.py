from jnpr.junos import Device
from lxml import etree
from jnpr.junos.utils.config import Config 
from os.path import exists
import yaml, os
from jnpr.junos.utils.sw import SW
import logging, json
from jnpr.junos.exception import ConnectError, ConnectAuthError, RpcError, ConfigLoadError, CommitError, LockError, RpcTimeoutError
from .path import create_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s:[%(levelname)s]:[%(name)s]:%(message)s")
file_handler = logging.FileHandler('jberry.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# logger.addHandler(stream_handler)

class JunosDevice:
    dump_path = None
    device_list_file = None
    dir_name = None

    def __init__(self, name, user, password, ip=None, console=None):
        self.name = name
        self.ip = ip 
        self.console = console
        self.user = user
        self.password = password
        self.dev = self.dev_connection(self.name, self.ip or self.console, self.user, self.password)

    def __repr__(self):
        return f"JunosDevice({self.name})"

    def connect(self):
        try:
            self.dev.open() 
        except ConnectAuthError as err:
            logger.error("[{}]: Invalid Username or password for device. {}".format(self.name, err))
            return -1
        except ConnectError as err:
            logger.error("[{}]: Could not connect to device. {}".format(self.name, err))
            return -2

    def disconnect(self):
        try:
            self.dev.close() 
        except Exception as err:
            logger.exception("[{}]: Exception caught for device. {}".format(self.name, err))
            return -99

    def __del__(self):
        pass

    @staticmethod
    def dev_connection(name, ip, user, password):
        logger.info(f'[{name}]: Connecting to device.')
        if ":" in ip:
            logger.info(f'[{name}]: Using Console for connection')
            return Device(host=ip.split(':')[0], mode='telnet', 
                    port=ip.split(':')[1], user=user, password=password, attempts=5, gather_facts=0)
        else:
            logger.info(f'[{name}]: Using IP for connection')
            return Device(host=ip, user=user, password=password, gather_facts=0)

    def __create_dir(self, module_name):
        return create_path(JunosDevice.dump_path, module_name, os.path.basename(JunosDevice.device_list_file))

    def write_to_file(self, file_name, contents):
        try:
            with open(file_name, 'w') as f:
                f.write(contents)
            return 0
        except FileNotFoundError:
            logger.error(f'[{name}]: {file} not found')

    def get_config(self, form, conf_xpath):
        logger.info(f'[{self.name}]: get_config called.')
        JunosDevice.dir_name = self.__create_dir('config')
        logger.info(f'[{self.name}]: Dump directory is {JunosDevice.dir_name}')
        try:
            self.connect()
            full_config = self.dev.rpc.get_config(filter_xml=conf_xpath, options={"format" : form})
            contents = etree.tostring(full_config, encoding="unicode", 
                pretty_print='True').replace(f'<configuration-{form}>', '').replace(f'</configuration-{form}>', '')
            file_name = JunosDevice.dir_name + self.name + "." + form
            self.write_to_file(file_name, contents)
            msg = self.name + "\n" + contents
            logger.debug(f'[{self.name}]: Dumping config ' + msg)
            self.disconnect()
            return 0
        except RpcError as err:
            logger.error("[{}]: Configuration hierarchy doesnt exist. {}".format(self.name, conf_xpath))
            return -3
        except ValueError as err:
            logger.error("[{}]: The filter is invalid. {}".format(self.name, conf_xpath))
            return -4
        except Exception as err:
            logger.exception("[{}]: Exception caught. {}".format(self.name, err))
            return -99

    def get_facts(self, key):
        try:
            self.connect()
            logger.info(f'[{self.name}]: get_facts called with key {key}')
            JunosDevice.dir_name = self.__create_dir('facts')
            logger.info(f'[{self.name}]: Dump directory is {JunosDevice.dir_name}')
            if key:
                contents = {}
                contents[key] = self.dev.facts[key]
            else:
                contents = self.dev.facts
            contents = json.dumps(contents)
            file_name = JunosDevice.dir_name + self.name + "_facts"
            self.write_to_file(file_name, contents)
            msg = json.dumps(contents)
            logger.debug(f'[{self.name}]: Dumping facts: {msg}')
            self.disconnect()
            return 0
        except KeyError as err:
            logger.error("[{}]: Fact {} doesnt exist. {}".format(self.name, key, err))
            return -6    
        except RuntimeError as err:
            logger.error("[{}]: Runtime Error. Could not connect to device. {}".format(self.name, err))
            return -7
        except Exception as err:
            logger.exception("[{}]: Exception caught. {}".format(self.name, err))
            return -99

    def load_config(self, conf, env_file, config_file_dir, template_path, form, overwrite):
        try:
            if config_file_dir:
                path = config_file_dir + "/" + self.name + "." + form
                logger.info(f'[{self.name}] : Loading config from {path}')
                conf.load(path=path, format=form, overwrite=overwrite)
                ret = conf
            elif env_file and template_path:
                with open(env_file, 'r') as ef:
                    env = yaml.safe_load(ef)
                    logger.info(f'[{self.name}] : Loading config from template {template_path} and vars file {env_file}')
                    temp = conf.load(template_path=template_path, template_vars=env, format=form)
                ret = conf
            else:
                ret = -11
            return ret
        except FileNotFoundError as err:
            logger.error(f"[{self.name}]: Failed to locate configuration file. {err}")
            return -11

    def set_config(self, env_file, config_file_dir, template_path, dry, form, overwrite=True):
        try:
            self.connect()
            logger.info(f'[{self.name}]: set_config called. Dry run: {dry}')
            JunosDevice.dir_name = self.__create_dir('delta')
            logger.info(f'[{self.name}]: Dump directory is {JunosDevice.dir_name}.')
            with Config(self.dev, mode="exclusive") as conf:
                ret = self.load_config(conf=conf, env_file=env_file, config_file_dir=config_file_dir, template_path=template_path, 
                                    form=form, overwrite=overwrite)
                if ret == -11:
                    logger.info(f"[{self.name}]: No env file or config file provided.")
                    return ret, self.name, None
                diff = conf.diff()
                if diff == None:
                    diff = "None"
                    ret = 0
                else:
                    ret = 1
                file_name = JunosDevice.dir_name + self.name + "." + form
                contents = diff
                self.write_to_file(file_name, contents)
                if not dry:
                    conf.commit()
                    msg = "Configuration commited for device {}".format(self.name)
                else:
                    msg = "{} Dry run completed. To skip dry run pass agrument '-d 0'".format(self.name)
            self.disconnect()
            logger.debug(f'[{self.name}]: Dumping diff: \n {diff}')
            logger.debug(msg)
            return ret, self.name, file_name
        except LockError as err:
            logger.error("[{}]: Failed to lock device. {}".format(self.name,err))
            return -8, self.name, None
        except CommitError as err:
            logger.error("[{}]: Failed to commit configuration. {}".format(self.name,err))
            return -9, self.name, None
        except ConfigLoadError as err:
            logger.error("[{}]: Failed to load configuration file. {}".format(self.name,err))
            return -10, self.name, None
        except RuntimeError as err:
            logger.error("[{}]: Failed to connect. {}".format(self.name,err))
            return -7, self.name, None
        except RpcTimeoutError as err:
            logger.error("[{}]: Rpc Timeout Error. {}".format(self.name,err))
            return -12, self.name, None
        except Exception as err:
            logger.exception("[{}]: Exception caught. {}".format(self.name, err))
            return -99, self.name, None

    def upgrade_junos(self, dry, package, validate, checksum_algorithm, remote_path):
        logger.info(f'[{self.name}]: upgrade_junos called.')
        logger.info(f'[{self.name}]: to be upgraded using package {package}. Dry run: {dry}')
        dev = self.dev_connection(self.name, self.ip or self.console, self.user, self.password)
        try:
            dev.open() 
            if not dry:
                "***{} UPGRADE STARTED***".format(self.name)
                sw = SW(dev)
                ok, msg = sw.install(package=package, validate=validate, remote_path=remote_path, 
                                    checksum_algorithm=checksum_algorithm)
                logger.info("status: " + str(ok) + ", Message: " + msg)
                if ok:
                    sw.reboot()
            else:
                logger.info("[{}]: Dry run completed. To skip dry run pass agrument '-d 0'".format(self.name))
            dev.close()
            logger.info(f"***[{self.name}]: UPGRADE FINISHED***")
            return 0
        except RuntimeError as err:
            logger.error("[{}]: Failed to connect to device. {}".format(self.name, err))
            return -7
        except ConnectAuthError as err:
            logger.error("[{}]: Invalid Username or password. {}".format(self.name, err))
            return -1
        except ConnectError as err:
            logger.error("[{}]: Could not connect to device. {}".format(self.name, err))
            return -2
        except Exception as err:
            logger.error("[{}]:Exception caught. {}".format(self.name, err))
            return -99

    def zeroize_junos(self, dry):
        logger.info(f'[{self.name}]: zeroize_junos called. Dry run: {dry}')
        dev = self.dev_connection(self.name, self.ip or self.console, self.user, self.password)
        try:
            dev.open() 
            if not dry:
                sw = SW(dev)
                msg = self.name + " " + sw.zeroize()
            else:
                msg = "[{}]: Dry run completed. To skip dry run pass agrument '-d 0'".format(self.name)
            logger.info(msg)
            dev.close()
            return 0
        except RuntimeError as err:
            logger.error("[{}]: Failed to connect to device. {}".format(self.name, err))
            return -7
        except ConnectAuthError as err:
            logger.error("[{}]: Invalid Username or password. {}".format(self.name, err))
            return -1
        except ConnectError as err:
            logger.error("[{}]: Could not connect. {}".format(self.name, err))
            return -2
        except Exception as err:
            logger.error("[{}]: Exception caught. {}".format(self.name, err))
            return -99

    def power_junos(self, power, t, dry):
        logger.info(f'[{self.name}]: power_junos called. Dry run: {dry}')
        logger.info(f"[{self.name}]: ACTION IS {power}")
        dev = self.dev_connection(self.name, self.ip or self.console, self.user, self.password)
        try:
            dev.open() 
            sw = SW(dev)
            if not dry:
                if power == "poweroff":
                    msg = sw.poweroff(in_min=t) + " [{}]".format(self.name)
                else:
                    msg = sw.reboot(in_min=t) + " [{}]".format(self.name)
            else:
                msg = "[{}]: Dry run completed. To skip dry run pass agrument '-d 0'".format(self.name)
            logger.info(msg)
            dev.close()
            return 0
        except RuntimeError as err:
            logger.error("[{}]: Failed to connect to device. {}".format(self.name, err))
            return -7
        except ConnectAuthError as err:
            logger.error("[{}]: Invalid Username or password. {}".format(self.name, err))
            return -1
        except ConnectError as err:
            logger.error("[{}]: Could not connect. {}".format(self.name, err))
            return -2
        except Exception as err:
            logger.error("[{}]:Exception caught. {}".format(self.name, err))
            return -99
