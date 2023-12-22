"""
Generates a list of Indigo methods for inspection

The list_of_indigo_methods method will generate a list of Indigo methods available for inspection. It is used to
populate the list of methods control for the Methods - Indigo Base... tool.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_methods(values_dict:indigo.Dict=None):
    """
    Generate a list of Indigo methods given a user-selected class

    :param indigo.Dict values_dict:
    :return:
    """
    return_value = []
    try:
        if len(values_dict.keys()) == 0:
            pass

        else:
            indigo_classes = getattr(indigo, values_dict['list_of_indigo_classes'])
            directory = dir(indigo_classes)

            if values_dict.get('include_hidden_methods', False):
                return_value = [_ for _ in directory]
            else:
                return_value = [_ for _ in directory if not _.startswith('_')]

    except AttributeError:
        pass

    return return_value
