"""
Return a list of Indigo objects for inspection

The dict_to_print method will return a list of objects for inspection. Objects that are supported include Actions,
Control Pages, Devices, Schedules, Triggers, and variables. It is called by the Object Dictionary... menu item in
conjunction with the results_output method.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def print_dict(values_dict:indigo.Dict=None):
    """
    Prints selected information about an Indigo object based on user-selected class and object

    :param indigo.Dict values_dict:
    :return:
    """
    if not values_dict:
        return_value = [("none", "None")]
    else:
        return_value = [
            (thing.id, thing.name) for thing in getattr(indigo, values_dict['classOfThing'])
        ]

    return return_value
