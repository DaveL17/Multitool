"""
Removes all delayed actions from the Indigo server

The remove_all_delayed_actions method is a convenience tool to remove all delayed actions from the Indigo server.
"""

import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def remove_actions():
    """
    Remove all delayed actions from the Indigo server

    :return:
    """
    indigo.server.removeAllDelayedActions()
    return True
