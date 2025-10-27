"""
Print list of Z-Wave devices and their current battery level
"""

import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(no_log: bool = False) -> None:
    """
    Print list of Z-Wave devices and their current battery levels

    Will return all known battery levels regardless of whether the device is enabled or configured.

    :return:
    """
    collection = {}

    # Gather all battery-powered devices and their battery levels
    for dev in indigo.devices.iter("indigo.zwave"):
        if dev.batteryLevel:
            collection[dev.name] = dev.batteryLevel

    if not no_log:
        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        indigo.server.log(f"{' Battery Level Report ':=^100}")
        if len(collection) == 0:
            indigo.server.log("No battery devices found.")
        else:
            longest_name = max(map(len, collection))
            for k, v in collection.items():
                indigo.server.log(f"{k:<{longest_name}} | {'-' * int(collection[k] / 2)}| {collection[k]}%")
