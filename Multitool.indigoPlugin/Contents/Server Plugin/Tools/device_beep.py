"""
Send a beep request to a device

The device_to_beep method will send a beep request to a selected Indigo device. Only select
devices support the beep request and only enabled devices are displayed for selection.

:param indigo.Dict values_dict:
:param int type_id:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")
ERR_MSG_DICT = indigo.Dict()


def __init__():
    pass


def beeper(values_dict):
    try:
        name = indigo.devices[int(values_dict['listOfDevices'])].name
        indigo.server.log(f"{' Send Beep to ' + name + ' ':{'='}^80}")
        indigo.device.beep(int(values_dict['listOfDevices']), suppressLogging=False)
        return True

    except ValueError:
        ERR_MSG_DICT['listOfDevices'] = "You must select a device to receive the beep request"
        ERR_MSG_DICT['showAlertText'] = "Beep Error.\n\nReason: No device selected."
        return False, values_dict, ERR_MSG_DICT
