"""
ping tool
"""

import logging
import os
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def do_the_ping(action, menu_call=False):
    """
    Conduct a simple ping to determine if a resource is up.

    :param indigo.actionGroup action:
    :param bool menu_call:
    :return:
    """
    dev_id: int = 0
    dev: indigo.device = None
    hostname: str = ""

    # Ping requested from plugin menu
    if menu_call:
        hostname = action['hostname']
        indigo.server.log(f"Network Ping requested from menu")
    # Ping requested from plugin action
    else:
        dev_id   = int(action.props['selected_device'])
        dev      = indigo.devices[dev_id]  # the ping device
        hostname = dev.ownerProps['hostname']

    # Do the ping
    response = os.system(f"/sbin/ping -c 1 {hostname}")

    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current logging
    # level.
    if response == 0:
        states_list = [{'key': 'status', 'value': True}]
        indigo.server.log(f"Ping host: {hostname} is up.")
    else:
        states_list = [{'key': 'status', 'value': False}]
        indigo.server.log(f"Ping host: {hostname} is down.")

    # If requested from menu, we don't have a device to update
    if menu_call:
        return

    dev.updateStatesOnServer(states_list)
