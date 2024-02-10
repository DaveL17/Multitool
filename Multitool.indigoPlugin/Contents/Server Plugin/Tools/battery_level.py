"""
Print list of Z-Wave devices and their current battery level
"""

import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(values_dict: indigo.Dict = None):
    """
    Print list of Z-Wave devices and their current battery levels

    :param indigo.Dict values_dict:
    :return:
    """
    collection = {}

    # Gather all battery-powered devices and their battery levels
    for dev in indigo.devices.iter("indigo.zwave"):
        if dev.batteryLevel:
            collection[dev.name] = dev.batteryLevel

    # Print report
    indigo.server.log(f"{' Battery Level Report ':=^100}")
    if len(collection) == 0:
        indigo.server.log("No battery devices found.")
    else:
        longest_name = max(map(len, collection))
        for k in collection:
            indigo.server.log(
                f"{k:<{longest_name}} | {'-' * int(collection[k] / 2)}| {collection[k]}%"
            )
    return True
