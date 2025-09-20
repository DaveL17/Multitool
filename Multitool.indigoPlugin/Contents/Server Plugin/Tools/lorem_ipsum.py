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
