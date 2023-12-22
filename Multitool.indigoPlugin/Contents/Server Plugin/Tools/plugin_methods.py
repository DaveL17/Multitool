"""
Generates a list of Indigo plugin methods for inspection

The list_of_plugin_methods method will generate a list of Indigo plugin methods available for inspection. It is used to
populate the list of methods control for the Methods - Plugin Base... tool.
"""
import logging
import inspect
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def list_methods(values_dict:indigo.Dict):
    """
    Generate a list of Indigo plugin methods for inspection

    :param indigo.Dict values_dict:
    """
    list_of_attributes = []

    for method in dir(indigo.PluginBase):
        try:
            inspect.getfullargspec(getattr(indigo.PluginBase, method))
            if values_dict.get('include_hidden_methods', False):
                list_of_attributes.append((method, f"self.{method}"))
            else:
                if not method.startswith('_'):
                    list_of_attributes.append((method, f"self.{method}"))

        except (AttributeError, TypeError):
            continue

    return list_of_attributes
