"""
Send a status request to an Indigo object

The send_status_request method will send a status request inquiry to a selected Indigo
object. Note that not all objects support a status request and plugin devices that support
status requests must have their host plugin enabled. Further, only enabled objects are
available for a status request.

:param indigo.Dict values_dict:
:param str type_id:
:return:
"""
import indigo
import logging

ERR_MSG_DICT = indigo.Dict()
LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def get_status(values_dict):
    try:
        indigo.server.log(f"{' Sending Status Request ':{'='}^80}")
        indigo.device.statusRequest(int(values_dict['listOfDevices']), suppressLogging=False)
        return values_dict

    except Exception as err:
        LOGGER.critical("Error sending status Request.")
        ERR_MSG_DICT['listOfDevices'] = "Problem communicating with the device."
        ERR_MSG_DICT['showAlertText'] = f"Status Request Error.\n\nReason: {err}"
        return False, values_dict, ERR_MSG_DICT
