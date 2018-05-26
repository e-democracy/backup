from dotenv import load_dotenv
from enum import Enum, unique
from os import getcwd, getenv, path


@unique
class ConfigKey(Enum):
    DATABASE_PATH = 'DATABASE_PATH'


def get_edem_env_name(config_enum):
    return "%s_EDEM_BACKUP_%s" % (EDEM_ENV, config_enum.value)


def get_edem_env_value(config_enum):
    return getenv(get_edem_env_name(config_enum))


# Load configurations
EDEM_ENV = getenv('EDEM_BACKUP_ENV', 'TEST').upper()
env_path = path.join(getcwd(), '.env')
load_dotenv(dotenv_path=env_path, verbose=True)
config = {name: get_edem_env_value(name) for name in ConfigKey}
