"""
Logs the inspection of the passed class/method

The log_of_method method will generate an inspection of the passed class and method (i.e.,
indigo.server.log) and write the result to the Indigo Activity Log.

:param indigo.Dict values_dict:
:param str type_id:
:return:
"""
import indigo
import logging
import inspect

lOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_inspection(values_dict):
    method_to_call = getattr(indigo, values_dict['list_of_indigo_classes'])
    method_to_call = getattr(method_to_call, values_dict['list_of_indigo_methods'])
    inspector = inspect.getdoc(method_to_call)
    indigo.server.log(f"\nindigo.{values_dict['list_of_indigo_classes']}.{inspector}")
