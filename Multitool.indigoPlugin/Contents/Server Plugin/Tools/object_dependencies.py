"""
Print an Indigo object's dependencies to the Indigo events log

The results_output method formats an object's *.dependencies() and outputs it to the Indigo events log. It's used in
conjunction with the Object Inspection... tool.
"""
import logging
from constants import INSTANCE_TO_COMMAND_NAMESPACE
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_results(values_dict:indigo.Dict=None, caller:str=""):
    """
    Prepare and output the dependency results to the Indigo events log.

    :param indigo.Dict values_dict:
    :param str caller:
    :return:
    """
    LOGGER.debug(f"Caller: {caller}")
    obj_id = int(values_dict['thingToPrint'])
    thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]

    try:
        indigo.server.log(f"{' ' + thing.name + ' Dependencies ':{'='}^80}")
        dep_dict = INSTANCE_TO_COMMAND_NAMESPACE[type(thing)].getDependencies(obj_id)  # Dict of object dependencies

        for obj_cat in dep_dict:
            indigo.server.log(f"{obj_cat}:")
            for dep in dep_dict[obj_cat]:
                indigo.server.log(f"   {len(dep)}")
                indigo.server.log(f"   {dep['Name']} ({dep['ID']})")

        indigo.server.log("=" * 80)
    except KeyError:
        LOGGER.warning("Object type not currently supported. Please provide a report so the plugin can be updated.")
