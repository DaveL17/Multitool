"""
Return a list of Indigo objects for inspection

The dict_to_print method will return a list of objects for inspection. Objects that are
supported include Actions, Control Pages, Devices, Schedules, Triggers, and variables. It
is called by the Object Dictionary... menu item in conjunction with the results_output
method.

:param str fltr:
:param indigo.Dict values_dict:
:param int target_id:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def print_dict(values_dict):
    if not values_dict:
        return_value = [("none", "None")]
    else:
        return_value = [
            (thing.id, thing.name) for thing in getattr(indigo, values_dict['classOfThing'])
        ]

    return return_value
