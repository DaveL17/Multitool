"""
Removes all delayed actions from the Indigo server

The remove_all_delayed_actions method is a convenience tool to remove all delayed actions
from the Indigo server.

:param indigo.Dict values_dict:
:param str type_id:
:return:
"""

import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def remove_actions():

    indigo.server.removeAllDelayedActions()
    return True
