"""
Generate an Indigo substitution string

The substitution_generator method is used to construct Indigo substitution string segments from Indigo objects.  For
example,

    Indigo Device Substitution: %%d:978421449:stateName%%
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")
ERR_MSG_DICT = indigo.Dict()


def __init__():
    pass


def get_substitute(values_dict: indigo.Dict = None):
    """
    Generate a substitution based on user input

    :param indigo.Dict values_dict:
    :return:
    """
    substitution_text = values_dict.get('thingToSubstitute', '')
    result = indigo.activePlugin.substitute(substitution_text)

    if substitution_text == '':
        return_value = (True, values_dict)

    elif result:
        indigo.server.log(result)
        return_value = (True, values_dict)

    else:
        ERR_MSG_DICT['thingToSubstitute'] = "Invalid substitution string."
        ERR_MSG_DICT['showAlertText'] = (
            "Substitution Error.\n\nYour substitution string is invalid. See the Indigo log "
            "for available information."
        )
        return_value = (False, values_dict, ERR_MSG_DICT)

    return return_value
