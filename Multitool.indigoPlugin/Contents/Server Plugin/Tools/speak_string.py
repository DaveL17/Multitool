"""
Speak a string

The speak_string method takes a user-input string and sends it for speech on the Indigo server. The method supports
Indigo substitutions and is useful when testing substitution strings.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")
ERR_MSG_DICT = indigo.Dict()


def __init__():
    pass


def speaker(values_dict:indigo.Dict=None):
    """
    The speak_string method takes a user-input string and sends it for speech on the Indigo server.

    :param indigo.Dict values_dict:
    :return:
    """
    text = values_dict['thingToSpeak']

    # If 'thingToSpeak' is an empty string
    if not text:
        ERR_MSG_DICT['thingToSpeak'] = "Required"
        return values_dict, ERR_MSG_DICT

    try:
        # Validate substitution string
        sub_test = indigo.activePlugin.substitute(text, validateOnly=True)
        if not sub_test[0]:
            raise Exception(sub_test[1])
        # Substitution string is valid.
        text_to_speak = indigo.activePlugin.substitute(text)
        indigo.server.log(f"{' Speaking ':=^80}")
        indigo.server.log(f"{text_to_speak}")
        indigo.server.speak(text_to_speak)
        return_value = values_dict

    except Exception as err:
        LOGGER.critical("Error speaking string. %s", err)
        ERR_MSG_DICT['thingToSpeak'] = "String to speak is invalid."
        return_value = (values_dict, ERR_MSG_DICT)

    return return_value
