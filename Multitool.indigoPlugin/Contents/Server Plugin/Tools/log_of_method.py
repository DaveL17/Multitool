"""
Logs the inspection of the passed class/method

The log_of_method method will generate an inspection of the passed class and method (i.e., indigo.server.log) and
write the result to the Indigo Activity Log.
"""
import logging
import inspect
try:
    import indigo
except ImportError:
    pass

lOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_inspection(values_dict:indigo.Dict=None):
    """
    Output an instpection of the passed class and object to the Indigo Events log

    :param indigo.Dict values_dict:
    :return:
    """
    method_to_call = getattr(indigo, values_dict['list_of_indigo_classes'])
    method_to_call = getattr(method_to_call, values_dict['list_of_indigo_methods'])
    inspector = inspect.getdoc(method_to_call)
    indigo.server.log(f"\nindigo.{values_dict['list_of_indigo_classes']}.{inspector}")

# TODO: Update this to improve the instances where the underlying item isn't callable.
# import inspect
#
# foo = inspect.getdoc(indigo.host.debugMode)  <== this is an example of something that's not callable.
# # indigo.server.log(f"{foo}")
# bar = callable(indigo.host.debugMode)
# indigo.server.log(f"{bar}")
