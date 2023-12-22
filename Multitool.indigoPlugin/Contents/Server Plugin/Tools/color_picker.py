"""
Print color information to the Indigo events log

Write color information to the Indigo events log to include the raw, hex, and RGB values.

:param indigo.Dict picker.values_dict:
:param int picker.type_id:
:return:
"""

try:
    import indigo
except ImportError:
    pass


def __init__():
    pass

def picker(values_dict:indigo.Dict=None, type_id:str=""):
    """
    Print raw, hex, and rgb color values to the Indigo events log

    :param indigo.Dict values_dict:
    :param str type_id:
    :return:
    """
    if not values_dict['chosenColor']:
        values_dict['chosenColor'] = "FF FF FF"
    indigo.server.log(f"Raw: {values_dict['chosenColor']}")
    indigo.server.log(f"Hex: #{values_dict['chosenColor'].replace(' ', '')}")
    indigo.server.log(
        f"RGB: {tuple([int(thing, 16) for thing in values_dict['chosenColor'].split(' ')])}"
    )
