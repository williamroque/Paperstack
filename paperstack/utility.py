"Module containing various utility functions."

import os
import platform
import subprocess


def open_path(path):
    """Open file at path using the default system application.

    Arguments
    ---------
    path : str
    """

    if platform.system() == 'Darwin':
        subprocess.call(
            ('open', path),
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
        )
    elif platform.system() == 'Windows':
        os.startfile(path)
    else:
        subprocess.call(
            ('xdg-open', path),
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
        )


def parse_dict(raw):
    """Parse string of type 'key1: value1; key2: value2; [...]' into
    dictionary.

    Parameters
    ----------
    raw : str

    Returns
    -------
    dict
    """

    raw = raw.replace('https://', '')

    parsed_dict = {}
    entries = raw.split(';')

    for entry in entries:
        if ':' in entry:
            key, value = entry.split(':')

            parsed_dict[key.strip()] = value.strip()

    return parsed_dict
