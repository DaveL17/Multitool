"""
Generate the construct for an Indigo substitution

The generator_substitutions method is used with the Substitution Generator. It is the callback that's used to create
the Indigo substitution construct.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def return_substitution(values_dict:indigo.Dict=None):
    """
    Generate an Indigo substitution string based on user-selected object

    :param indigo.Dict values_dict:
    :return:
    """
    dev_var_id = values_dict['devVarMenu']
    dev_var_value = values_dict['generator_state_or_value']

    if int(values_dict['devVarMenu']) in indigo.devices.keys():
        indigo.server.log(f"Indigo Device Substitution: %%d:{dev_var_id}:{dev_var_value}%%")

    else:
        indigo.server.log(f"Indigo Variable Substitution: %%v:{dev_var_id}%%")

    values_dict['devVarMenu'] = ''
    values_dict['generator_state_or_value'] = ''

    return values_dict
