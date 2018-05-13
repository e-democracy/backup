import configparser
from os import getenv

SCRIPT_CONFIG_PATH = 'config/script.conf'

# Load configurations
EDEM_ENV = getenv('EDEM_ENV', 'test')
all_config = configparser.ConfigParser()
all_config.read(SCRIPT_CONFIG_PATH)

config = all_config[EDEM_ENV]
