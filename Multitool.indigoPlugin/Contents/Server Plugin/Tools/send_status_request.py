"""
Send a status request to an Indigo object

The send_status_request method will send a status request inquiry to a selected Indigo object. Note that not all
objects support a status request and plugin devices that support status requests must have their host plugin enabled.
Further, only enabled objects are available for a status request.
"""
import logging
import indigo  # noqa

ERR_MSG_DICT = indigo.Dict()
LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def get_status(values_dict: indigo.Dict = None):
    """
    Send a status request to the user-specified device

    :param indigo.Dict values_dict:
    :return:
    """
    try:
        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        indigo.server.log(f"{' Sending Status Request ':{'='}^80}")
        indigo.device.statusRequest(int(values_dict['listOfDevices']), suppressLogging=False)
        return values_dict

    except Exception as err:
        LOGGER.critical("Error sending status Request.")
        ERR_MSG_DICT['listOfDevices'] = "Problem communicating with the device."
        ERR_MSG_DICT['showAlertText'] = f"Status Request Error.\n\nReason: {err}"
        return False, values_dict, ERR_MSG_DICT
