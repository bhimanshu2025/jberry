import unittest
from unittest.mock import patch, MagicMock
import os, sys
from jnpr.junos.exception import ConnectError, ConnectAuthError, RpcError, ConfigLoadError, CommitError, LockError, RpcTimeoutError
sys.path.append( '/root/jberry/python/' )
from utils.junosDevice import JunosDevice

class TestjunosDevice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.makedirs('/root/backups1/', exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        os.system('rm -rf /root/backups1')

    def setUp(self):
        self.JD1 = JunosDevice("qfx", "root", "Juniper", "10.85.3.148")
        self.JD2 = JunosDevice("qfx", "root", "Juniper1", "10.85.3.148")
        self.JD3 = JunosDevice("qfx", "root", "Juniper", "10.85.3.149")
        JunosDevice.dump_path = "/root/backups1/"
        JunosDevice.device_list_file = "Quincy.yml"   

    def tearDown(self):
        pass


    def test_get_config(self):
        with patch.object(self.JD1, 'dev') as mocked_dev:
            with patch('utils.junosDevice.etree') as patched_etree:
                patched_etree.tostring.return_value = '<configuration-text>xyz</configuration-text>'
                self.assertEqual(self.JD1.get_config('set', None), 0)
                mocked_dev.rpc.get_config.side_effect = RpcError('rpc err')
                self.assertEqual(self.JD1.get_config('set', None), -3)
                mocked_dev.rpc.get_config.side_effect = ValueError('value err')
                self.assertEqual(self.JD1.get_config('set', None), -4)
                mocked_dev.rpc.get_config.side_effect = Exception('err')
                self.assertEqual(self.JD1.get_config('set', None), -99)

    def test_get_facts(self):
        with patch.object(self.JD1, 'dev' ) as mocked_dev:
            mocked_dev.facts = {'model': 'srx100'}
            self.assertEqual(self.JD1.get_facts('model'), 0)
            self.assertEqual(self.JD1.get_facts(None), 0)
            self.assertEqual(self.JD1.get_facts('model1'), -6)
            with patch.object(self.JD1, 'disconnect') as mocked_disconnect:
                mocked_disconnect.side_effect = RuntimeError('runtime err')
                self.assertEqual(self.JD1.get_facts('model'), -7)
                mocked_disconnect.side_effect = Exception('err')
                self.assertEqual(self.JD1.get_facts('model'), -99)

    def test_set_config(self):
        config_file_dir = "/root"
        dry = 0
        form = "text"
        with patch.object(self.JD1, 'dev' ) as mocked_dev:
            with patch('utils.junosDevice.Config', name="m1") as mocked_config:
                with patch.object(self.JD1, 'write_to_file') as mocked_write_to_file:
                    instance = mocked_config.return_value
                    instance.return_value = None
                    self.assertEqual(self.JD1.set_config(None, None, None, dry, form), -11)
                    self.assertEqual(self.JD1.set_config(None, '/tmp', None, dry, form), 1)
                    # self.assertEqual(self.JD1.set_config(None, '/tmp', None, dry, form), 0) # needs further work. 
                    # I am not able to mock conf.diff() instance even though Config.diff() gets mocked
                
    # def test_connect(self):
    #     with patch.object(self.JD1, 'dev' ) as mocked_dev:
    #         with patch('utils.junosDevice.logging') as mocked_logger:

    #             mocked_dev.open.side_effect = ConnectError("Connection Error")
    #             self.assertEqual(self.JD1.connect(), -2)


if __name__ == "__main__":
    unittest.main()