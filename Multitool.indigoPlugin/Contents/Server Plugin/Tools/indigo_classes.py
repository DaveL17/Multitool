"""
Generates a list of Indigo classes for inspection

The list_of_indigo_classes method will generate a list of Indigo classes available for inspection. It is used to
populate the list of classes control for the Methods - Indigo Base... tool.
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_classes(values_dict: indigo.Dict = None) -> list:
    """

    :param indigo.Dict values_dict:
    :return:
    """
    # If user elects to display hidden methods.
    if values_dict.get('include_hidden_methods', False):
        result = [(f"{_}", f"indigo.{_}") for _ in sorted(dir(indigo), key=str.lower)]
    else:
        result = [
            (f"{_}", f"indigo.{_}") for _ in sorted(dir(indigo), key=str.lower)
            if not _.startswith('_')
        ]

    return result
