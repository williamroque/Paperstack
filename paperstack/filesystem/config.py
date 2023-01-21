"Home to the `Config` class. This is where configuration is done."

import configparser

from paperstack.filesystem.file import File


DEFAULT_CONFIG = {
    'paths': {
        'data': '~/Documents/Paperstack/'
    }
}


class Config:
    """Configuration class. Here we manage the configuration file and any
    read/write access.

    Parameters
    ----------
    config_path : str, optional
        Path to config file. If not specified, will look in home directory.

    Attributes
    ----------
    config_path : str
    """

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = '~/.paperstack.cfg'

        self.config_file = File(config_path)
        self.config_file.ensure()

        self.config = configparser.ConfigParser()
        self.config.read_dict(DEFAULT_CONFIG)
        self.config.read(self.config_file.path)


    def get(self, section, key):
        """Get value corresponding to a configuration item.

        Parameters
        ----------
        section : str
        key : str

        Returns
        -------
        str
            Value of config item.
        """

        return self.config[section][key]


    def update(self, section, key, value):
        """Update an item in the configuration (not written automatically).

        Parameters
        ----------
        section : str
        key : str
        value : str
        """

        self.config[section][key] = value


    def write(self):
        "Write configuration to file."

        with open(self.config_file.path, 'w') as f:
            self.config.write(f)
