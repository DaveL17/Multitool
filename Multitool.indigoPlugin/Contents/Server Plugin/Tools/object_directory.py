"""
Print an Indigo object's directory to the Indigo events log

The results_output method formats an object's dir() and outputs it to the Indigo events log. It's
used in conjunction with the Object Directory... tool.
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_results(values_dict, caller):
    """

    :param values_dict:
    :param caller:
    :return:
    """
    LOGGER.debug(f"Caller: {caller}")

    thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]
    indigo.server.log(f"{' ' + thing.name + ' ':{'='}^80}")
    indigo.server.log(f"\n{dir(thing)}")
    indigo.server.log("=" * 80)
