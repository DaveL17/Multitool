"""
Send a beep request to a device

The device_to_beep method will send a beep request to a selected Indigo device. Only select devices support the beep
request and only enabled devices are displayed for selection.
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")
ERR_MSG_DICT = indigo.Dict()


def __init__():
    pass


def beeper(values_dict: indigo.Dict = None):
    """
    Send a beep command to the selected device

    Note that beep is not a valid command for all devices.

    :param indigo.Dict values_dict:
    """
    try:
        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        name = indigo.devices[int(values_dict['listOfDevices'])].name
        indigo.server.log(f"{' Send Beep to ' + name + ' ':{'='}^80}")
        indigo.device.beep(int(values_dict['listOfDevices']), suppressLogging=False)
        return True

    except ValueError:
        ERR_MSG_DICT['listOfDevices'] = "You must select a device to receive the beep request"
        ERR_MSG_DICT['showAlertText'] = "Beep Error.\n\nReason: No device selected."
        return False, values_dict, ERR_MSG_DICT
