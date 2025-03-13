"""
Utility Function to Output Lorem Ipsum text.

credit: https://github.com/sfischer13/python-lorem
"""

import logging
import indigo  # noqa
try:
    import lorem  # noqa
except ImportError:
    indigo.server.log('The "lorem" library is required for this plugin.')

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(values_dict: indigo.Dict(), no_log: bool = False) -> None:
    """
    Prints lorem text to the Indigo Events Log

    :return:
    """
    LOGGER.info("=====================================  Lorem Ipsum Output  =====================================")

    # Prints one sentence of text.
    if values_dict['text_level'] == 'sentence':
        LOGGER.info(f"{lorem.sentence()}")
    # Prints one paragraph of text.
    elif values_dict['text_level'] == 'paragraph':
        LOGGER.info(f"{lorem.paragraph()}")
    #  Prints multiple paragraphs of text.
    elif values_dict['text_level'] == 'text':
        LOGGER.info(f"{lorem.text()}")

    # TODO: any need to do a more complex example?
    # from lorem.text import TextLorem
    #
    # # separate words by '-'
    # # sentence length should be between 2 and 3
    # # choose words from A, B, C and D
    # lorem = TextLorem(wsep='-', srange=(2, 3), words="A B C D".split())
    #
    # s1 = lorem.sentence()  # 'C-B.'
    # s2 = lorem.sentence()  # 'C-A-C.'
