"Text processing utilities."

import re


def clean_text(text):
    """Clean text from BibTeX entry.

    Parameters
    ----------
    text : str
    """

    accents = [
        ('`', 'a', 'à'),
        ('`', 'e', 'è'),
        ('`', 'i', 'ì'),
        ('`', 'o', 'ò'),
        ('`', 'u', 'ù'),

        ('\'', 'a', 'á'),
        ('\'', 'e', 'é'),
        ('\'', 'i', 'í'),
        ('\'', 'o', 'ó'),
        ('\'', 'u', 'ú'),

        ('"', 'a', 'ä'),
        ('"', 'e', 'ë'),
        ('"', 'i', 'ï'),
        ('"', 'o', 'ö'),
        ('"', 'u', 'ü'),

        ('\\^', 'a', 'â'),
        ('\\^', 'e', 'ê'),
        ('\\^', 'i', 'î'),
        ('\\^', 'o', 'ô'),
        ('\\^', 'u', 'û'),

        ('~', 'a', 'ã'),
        ('~', 'o', 'õ'),
        ('~', 'n', 'ñ'),

        ('c', 'c', 'ç'),
    ]

    template = r'\\{accent}{letter}|{{\\{accent}{letter}}}|\\{accent}{{{letter}}}'

    for accent, letter, sub in accents:
        text = re.sub(
            template.format(accent = accent, letter = letter),
            sub, text
        )
        text = re.sub(
            template.format(accent = accent, letter = letter.upper()),
            sub.upper(), text
        )

    text = re.sub(r'^{(.*)}$', '\\1', text)
    text = re.sub(r'{(.*?)}', '\\1', text)
    text = re.sub(r'\.~', '. ', text)

    return text
