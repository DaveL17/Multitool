"""
Print the signature of an Indigo method to the Indigo events log

The inspect_method method will inspect a selected Indigo method and print the target method's signature to the Indigo
events log. This is useful when the signature of an Indigo method is unknown.  It will return a list of attributes
passed by the Indigo method.  For example,

   Multitool    self.closedPrefsConfigUi: ArgSpec(args=['self', 'valuesDict',
                'userCancelled'], varargs=None, keywords=None, defaults=None)
   Multitool    Docstring:  User closes config menu.
                The validatePrefsConfigUI() method will also be called.
"""
import logging
import inspect
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_docstring(values_dict: indigo.Dict = None) -> None:
    """

    :param indigo.Dict values_dict:
    :return:
    """
    try:
        method = getattr(indigo.activePlugin, values_dict['list_of_plugin_methods'])
    except (AttributeError, KeyError, TypeError):
        LOGGER.warning("No method selected, or the selected method no longer exists.")
        return

    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
    # logging level.
    try:
        signature = inspect.getfullargspec(method)
    except TypeError:
        signature = "(signature unavailable for this method)"
    indigo.server.log(f"self.{values_dict['list_of_plugin_methods']}: {signature}")
    indigo.server.log(f"Docstring: {method.__doc__}", isError=False)
