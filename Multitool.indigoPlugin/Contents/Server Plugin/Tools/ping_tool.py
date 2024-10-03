"""
ping tool
"""

import logging
import os
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def do_the_ping(action):
    """ Conduct a simple ping to determine if a resource is up. """
    dev_id   = int(action.props['selected_device'])
    dev      = indigo.devices[dev_id]  # the ping device
    hostname = dev.ownerProps['hostname']

    response = os.system(f"/sbin/ping -c 1 {hostname}")

    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current logging
    # level.
    if response == 0:
        states_list = [{'key': 'status', 'value': True}]
        indigo.server.log(f"Ping host: {hostname} is up.")
    else:
        states_list = [{'key': 'status', 'value': False}]
        indigo.server.log(f"Ping host: {hostname} is down.")

    dev.updateStatesOnServer(states_list)

# TODO: Finish the ping event.
