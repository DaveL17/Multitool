"""
Print color information to the Indigo events log

Write color information to the Indigo events log to include the raw, hex, and RGB values.

:param indigo.Dict picker.values_dict:
:param int picker.type_id:
:return:
"""

import logging
import indigo  # noqa

logger = logging.getLogger("Plugin")


def __init__():
    pass


def picker(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False):
    """
    Print raw, hex, and rgb color values to the Indigo events log

    :param indigo.Dict values_dict:
    :param str type_id:
    :param bool no_log:
    :return:
    """
    try:
        logger.debug(f"values_dict: {values_dict}")
        if not values_dict['chosenColor']:
            values_dict['chosenColor'] = "FF FF FF"

        if not no_log:
            # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
            # logging level.
            indigo.server.log(f"Raw: {values_dict['chosenColor']}")
            indigo.server.log(f"Hex: #{values_dict['chosenColor'].replace(' ', '')}")
            indigo.server.log(f"RGB: {tuple([int(thing, 16) for thing in values_dict['chosenColor'].split(' ')])}")
    except (AttributeError, ValueError) as err:
        logger.warning("Can not convert: input value %s is wrong type." % values_dict['chosenColor'])
