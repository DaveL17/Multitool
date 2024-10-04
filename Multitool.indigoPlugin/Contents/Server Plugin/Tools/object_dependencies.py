"""
Print an Indigo object's dependencies to the Indigo events log

The results_output method formats an object's *.dependencies() and outputs it to the Indigo events log. It's used in
conjunction with the Object Inspection... tool.
"""
import logging
from constants import INSTANCE_TO_COMMAND_NAMESPACE
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_results(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> None:
    """
    Prepare and output the dependency results to the Indigo events log.

    :param indigo.Dict values_dict:
    :param str caller:
    :param bool no_log: If True, no output is logged.
    :return:
    """
    dep_dict = {}
    obj_id = int(values_dict['thingToPrint'])
    thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]

    try:
        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        dep_dict = INSTANCE_TO_COMMAND_NAMESPACE[type(thing)].getDependencies(obj_id)  # Dict of object dependencies

    except KeyError:
        LOGGER.warning("Object type not currently supported. Please provide a report so the plugin can be updated.")

    if not no_log:
        indigo.server.log(f"{' ' + thing.name + ' Dependencies ':{'='}^80}")
        for obj_cat in dep_dict:
            indigo.server.log(f"{obj_cat}:")
            for dep in dep_dict[obj_cat]:
                indigo.server.log(f"   {len(dep)}")
                indigo.server.log(f"   {dep['Name']} ({dep['ID']})")

        indigo.server.log("=" * 80)
