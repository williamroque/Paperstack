"Module containing various utility functions."

import os
import re
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


def parse_dict(raw, default_key=None):
    """Parse string of type 'key1: value1; key2: value2; [...]' into
    dictionary.

    Parameters
    ----------
    raw : str
    default_key : str
        If an entry appears without a key, use this as the default.

    Returns
    -------
    dict
    """

    parsed_dict = {}
    entries = raw.split(';')

    for entry in entries:
        if ':' in entry:
            items = re.split(r'(?<!https)(?<!http):', entry)

            if len(items) == 2:
                key, value = items

                parsed_dict[key.strip()] = value.strip()
        elif default_key and entry:
            parsed_dict[default_key] = entry

    return parsed_dict
