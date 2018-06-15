import unittest
from mock import patch
import os

from backup.config import Config, ConfigKey


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        Config.config = None

    @patch('backup.config.Config.load', wraps=Config.load)
    def test_get_calls_load_when_needed(self, load):

        try:
            Config.get('foo')
        except KeyError:
            pass

        load.assert_called_once()

        load.reset_mock()
        try:
            Config.get('foo')
        except KeyError:
            pass

        load.assert_not_called()

    def test_values_can_be_set_by_environment(self):
        for key in ConfigKey:
            os.environ["TEST_EDEM_BACKUP_%s" % key.value] = "%s_VALUE" % \
                                                            key.value

        for key in ConfigKey:
            self.assertEqual(Config.get(key), "%s_VALUE" % key.value)

    def test_values_can_be_set(self):
        Config.set(ConfigKey.USERNAME, 'testValue')
        self.assertEqual(Config.get(ConfigKey.USERNAME), 'testValue')

    @patch('backup.config.load_dotenv')
    def test_load_loads_dotenv(self, mock_load_dotenv):
        Config.load()
        mock_load_dotenv.assert_called_once()
