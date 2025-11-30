"""
Send a ping request to a device

The pinger method will send a ping request to a selected Indigo device. Only enabled devices are displayed. Plugin
devices must support sendDevicePing method and plugin must be enabled.
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def pinger(values_dict: indigo.Dict = None) -> None:
    """
    Send a ping to the selected device. Only Z-Wave or INSTEON devices are supported by the built-in ping command, so
    one or both of these interface plugins must be enabled.

    :param indigo.Dict values_dict:
    :return:
    """
    dev_id = int(values_dict['listOfDevices'])
    dev = indigo.devices[dev_id]

    plugin_id = "com.perceptiveautomation.indigoplugin.InsteonCommands"
    plugin = indigo.server.getPlugin(plugin_id)
    insteon_enabled = plugin.isEnabled()

    plugin_id = "com.perceptiveautomation.indigoplugin.zwave"
    plugin = indigo.server.getPlugin(plugin_id)
    zwave_enabled = plugin.isEnabled()

    try:
        if insteon_enabled or zwave_enabled:
            if dev.enabled and dev.configured:
                # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's
                # current logging level.
                indigo.server.log(f" {'Pinging device: ' + dev.name:{'='}^80} ")
                result = indigo.device.ping(dev_id, suppressLogging=False)
                if result['Success']:
                    indigo.server.log(f"Ping \"{dev.name}\" success. Time: {result['TimeDelta'] / 1000.0} seconds.")
                else:
                    indigo.server.log("Ping fail.")
        else:
            LOGGER.warning("You must enable either or both: Z-Wave or INSTEON interfaces.")
    except (ValueError, TypeError):
        LOGGER.critical("Error: ", exc_info=True)
        LOGGER.critical("Error sending ping.")
