"""
Print a list of device dependencies to the Indigo events log

The device_dependencies method prints a list of known dependencies for a selected Indigo
device.

This tool has been subsumed under the Object Inspection Tool and can be deleted.  fixme
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def dependencies(values_dict):
    err_msg_dict = indigo.Dict()
    try:
        dev_id = int(values_dict['listOfDevices'])
        deps = indigo.device.getDependencies(dev_id)
        name = indigo.devices[dev_id].name
        indigo.server.log(f"{' ' + name + ' Dependencies':{'='}^80}")
        indigo.server.log(f"{deps}")
        return_value = values_dict

    except KeyError:
        LOGGER.critical("Device ID not found.")
        err_msg_dict['listOfDevices'] = "Device ID not found."
        return_value = values_dict, err_msg_dict

    except Exception as err:
        LOGGER.critical("Error: ", exc_info=True)
        err_msg_dict['listOfDevices'] = "Problem communicating with the device."
        err_msg_dict['showAlertText'] = f"Device dependencies Error.\n\nReason: {err}"
        return_value = values_dict, err_msg_dict

    return return_value
