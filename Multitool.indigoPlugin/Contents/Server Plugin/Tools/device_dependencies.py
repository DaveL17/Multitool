"""
Print a list of device dependencies to the Indigo events log

The device_dependencies method prints a list of known dependencies for a selected Indigo
device.

:param indigo.Dict values_dict:
:param int type_id:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")

def __init__():
    pass


def dependencies(values_dict):
    try:
        deps = indigo.device.getDependencies(int(values_dict['listOfDevices']))
        name = indigo.devices[int(values_dict['listOfDevices'])].name
        indigo.server.log(f"{' ' + name + ' Dependencies':{'='}^80}")
        indigo.server.log(f"{deps}")
        return_value = values_dict

    except Exception as err:
        err_msg_dict = indigo.Dict()
        LOGGER.critical("Error: ", exc_info=True)
        err_msg_dict['listOfDevices'] = "Problem communicating with the device."
        err_msg_dict['showAlertText'] = f"Device dependencies Error.\n\nReason: {err}"
        return_value = (values_dict, err_msg_dict)

    return return_value
