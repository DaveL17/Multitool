"""
Print an Indigo object's directory to the Indigo events log

The results_output method formats an object's dir() and outputs it to the Indigo events log. It's used in conjunction
with the Object Directory... tool.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_results(values_dict:indigo.Dict=None, caller:str=""):
    """
    Get a Python dir() of the user-specified object and output to the Indigo Events log

    :param indigo.Dict values_dict:
    :param str caller:
    :return:
    """
    LOGGER.debug(f"Caller: {caller}")

    thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]
    indigo.server.log(f"{' ' + thing.name + ' ':{'='}^80}")
    indigo.server.log(f"\n{dir(thing)}")
    indigo.server.log("=" * 80)
