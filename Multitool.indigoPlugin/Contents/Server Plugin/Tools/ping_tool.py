"""
Tool to send ping request to user-specified hostname

The call can come from a plugin action that requests ping for configured device or from a menu item call. Because menu
calls block, the timeout is limited to 5 seconds.
"""

import logging
import os
from datetime import datetime as dt
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def do_the_ping(action, menu_call: bool = False, no_log: bool = False):
    """
    Conduct a simple ping to determine if a resource is up.

    :param indigo.actionGroup action:
    :param bool menu_call:
    :param bool no_log:
    :return:
    """
    dev: indigo.device = None
    # dev_id: int = 0
    # hostname: str = ""
    # timeout: int = 0

    # Ping requested from plugin menu
    if menu_call:
        hostname = action['hostname']
        timeout = int(action.get('timeout', '5'))
        # Limit timeouts to 5 seconds.
        if timeout > 5:
            LOGGER.warning("Pings from the plugin menu are limited to 5 seconds.")
            LOGGER.warning("Limiting ping to 5 seconds.")
            timeout = 5
        if not no_log:
            indigo.server.log(f"Network Ping requested from menu")
    # Ping requested from plugin action
    else:
        dev_id = int(action.props['selected_device'])
        dev = indigo.devices[dev_id]  # the ping device
        if dev.enabled and dev.configured:
            hostname = dev.ownerProps['hostname']
            timeout = int(dev.ownerProps.get('timeout', '5'))
        else:
            indigo.server.log("The ping device must be enabled and configured.", level=logging.WARNING)
            return

    # Do the ping
    check_time = int(dt.now().timestamp())
    response = os.system(f"/sbin/ping -c 1 -t {timeout} {hostname}")

    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current logging
    # level.
    if response == 0:
        states_list = [{'key': 'status', 'value': True, 'uiValue': "Up"},
                       {'key': 'last_checked', 'value': check_time}
                       ]
        if not no_log:
            indigo.server.log(f"Network Ping host: {hostname} is up.")
    else:
        states_list = [{'key': 'status', 'value': False, 'uiValue': "Down"},
                       {'key': 'last_checked', 'value': check_time}
                       ]
        if not no_log:
            indigo.server.log(f"Network Ping host: {hostname} is down.")

    # If requested from menu, we don't have a device to update
    if menu_call:
        return

    # We do this every time as users may change the hostname of the device.
    new_props = dev.pluginProps
    new_props['address'] = hostname
    dev.replacePluginPropsOnServer(new_props)
    dev.updateStatesOnServer(states_list)
