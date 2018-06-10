import unittest
from mock import patch

from backup.config import Config


class ConfigTestCase(unittest.TestCase):

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
        pass

    def test_values_can_be_set_by_dotenv(self):
        pass
