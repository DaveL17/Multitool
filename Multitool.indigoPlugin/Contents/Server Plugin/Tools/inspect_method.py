"""
Print the signature of an Indigo method to the Indigo events log

The inspect_method method will inspect a selected Indigo method and print the target
method's signature to the Indigo events log. This is useful when the signature of an Indigo
method is unknown.  It will return a list of attributes passed by the Indigo method.  For
example,

   Multitool    self.closedPrefsConfigUi: ArgSpec(args=['self', 'valuesDict',
                'userCancelled'], varargs=None, keywords=None, defaults=None)
   Multitool    Docstring:  User closes config menu.
                The validatePrefsConfigUI() method will also be called.

:param indigo.Dict values_dict:
:param str type_id:
:return:
"""
import indigo
import logging
import inspect

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_docstring(values_dict):

    method = getattr(indigo.activePlugin, values_dict['list_of_plugin_methods'])
    signature = inspect.getfullargspec(method)
    indigo.server.log(f"self.{values_dict['list_of_plugin_methods']}: {signature}")
    doc_string = getattr(indigo.activePlugin, values_dict['list_of_plugin_methods']).__doc__
    indigo.server.log(f"Docstring: {doc_string}", isError=False)
