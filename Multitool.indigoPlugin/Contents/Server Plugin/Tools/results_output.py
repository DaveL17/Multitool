"""
Print an Indigo object's properties dict to the Indigo events log

The results_output method formats an object properties dictionary for output to the Indigo
events log. It's used in conjunction with the Object Dictionary... tool.

:param indigo.Dict values_dict:
:param str caller:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_results(values_dict, caller):
    LOGGER.debug(f"Caller: {caller}")

    thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]
    indigo.server.log(f"{thing.name:{'='}^80}")
    indigo.server.log(f"\n{thing}")
    indigo.server.log("=" * 80)
