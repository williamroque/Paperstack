"Module containing various utility functions."


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

    parsed_dict = {}
    entries = raw.split(';')

    for entry in entries:
        if ':' in entry:
            key, value = entry.split(':')

            parsed_dict[key.strip()] = value.strip()

    return parsed_dict
