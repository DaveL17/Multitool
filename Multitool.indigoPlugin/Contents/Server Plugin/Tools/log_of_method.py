"""
Logs the inspection of the passed class/method

The log_of_method method will generate an inspection of the passed class and method (i.e., indigo.server.log) and
write the result to the Indigo Activity Log.
"""
import logging
import inspect
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_inspection(values_dict: indigo.Dict = None) -> None:
    """
    Output an inspection of the passed class and object to the Indigo Events log

    :param indigo.Dict values_dict:
    :return:
    """
    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
    # logging level.
    method_to_call = getattr(indigo, values_dict['list_of_indigo_classes'])
    method_to_call = getattr(method_to_call, values_dict['list_of_indigo_methods'])
    inspector = inspect.getdoc(method_to_call)
    indigo.server.log(f"\nindigo.{values_dict['list_of_indigo_classes']}.{inspector}")

# TODO: Update this to improve the instances where the underlying item isn't callable.
# import inspect
#
# get_attrib_dict = inspect.getdoc(indigo.host.debugMode)  <== this is an example of something that's not callable.
# # indigo.server.log(f"{get_attrib_dict}")
# bar = callable(indigo.host.debugMode)
# indigo.server.log(f"{bar}")
