"""
Send a ping request to a device

The pinger method will send a ping request to a selected Indigo device. Only enabled devices are displayed. Plugin
devices must support sendDevicePing method and plugin must be enabled.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def pinger(values_dict:indigo.Dict=None):
    """
    Send a ping to the selected device

    :param indigo.Dict values_dict:
    :return:
    """
    dev_id = int(values_dict['listOfDevices'])
    dev = indigo.devices[dev_id]

    try:
        if dev.enabled:
            indigo.server.log(f"{'Pinging device: ' + dev.name:{'='}^80}")
            result = indigo.device.ping(dev_id, suppressLogging=False)
            if result['Success']:
                indigo.server.log(
                    f"Ping \"{dev.name}\" success. Time: {result['TimeDelta'] / 1000.0} seconds."
                )
            else:
                indigo.server.log("Ping fail.")
    except (ValueError, TypeError):
        LOGGER.critical("Error: ", exc_info=True)
        LOGGER.critical("Error sending ping.")
