"""
Print list of Z-Wave devices and their current battery level
"""

import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(no_log: bool = False) -> str:
    """
    Print list of Z-Wave devices and their current battery levels

    Will return all known battery levels regardless of whether the device is enabled or configured.

    :param no_log: If True output will not be sent to the Indigo Events Log
    :return:
    """
    collection = {}
    batt_report: str = f"{' Battery Level Report ':=^85}\n"

    # Gather all battery-powered devices and their battery levels
    for dev in indigo.devices.iter("indigo.zwave"):
        if dev.batteryLevel:
            collection[dev.name] = dev.batteryLevel

    if len(collection) == 0:
        batt_report += "No battery devices found."
    else:
        longest_name = min(max(map(len, collection)), 40)
        for k, v in collection.items():
            name = k if len(k) <= 40 else k[:37] + "..."
            batt_report += f"{name:<{longest_name}} | {'-' * int(collection[k] / 2)}| {collection[k]}%\n"

    if no_log:
        # send to caller
        return batt_report
    else:
        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        for line in batt_report.splitlines():
            indigo.server.log(line)
        return batt_report
