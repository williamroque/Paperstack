"Home to the `Config` class. This is where configuration is done."

import configparser
import os

from paperstack.filesystem.file import File


DEFAULT_CONFIG = {
    'paths': {
        'data': '~/Documents/Paperstack/'
    },
    'article': {
        'id-format': 'author@2-title@10-year@4'
    },
    'ads': {
        'key': '',
        'timeout': 10
    },
    'arxiv': {
        'timeout': 10
    },
    'mnras': {
        'timeout': 10
    },
    'keys': {
        'vim-bindings': 'no'
    },
    'editor': {
        'command': 'vi',
        'extension': 'md'
    }
}


class Config:
    """Configuration class. Here we manage the configuration file and any
    read/write access.

    Parameters
    ----------
    messenger : paperstack.interface.message.Messenger
    config_path : str, optional
        Path to config file. If not specified, will look in home directory.

    Attributes
    ----------
    messenger : paperstack.interface.message.Messenger
    config_file : paperstack.filesystem.file.File
    config : configparser.ConfigParser
    """

    def __init__(self, messenger, config_path=None):
        self.messenger = messenger

        if config_path is None:
            if 'PAPERSTACKCONFIG' in os.environ:
                config_path = os.environ['PAPERSTACKCONFIG']
            else:
                config_path = '~/.paperstack.cfg'

        self.config_file = File(config_path)
        self.config_file.ensure()

        self.config = configparser.ConfigParser()
        self.config.read_dict(DEFAULT_CONFIG)

        try:
            self.config.read(self.config_file.path)
        except configparser.Error:
            self.messenger.send_warning('Damaged config file.')


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
