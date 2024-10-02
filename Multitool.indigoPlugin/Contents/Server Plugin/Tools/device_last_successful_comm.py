"""
Print information on the last successful communication with a device

The device_last_successful_comm method prints information on the last successful
communication with each Indigo device to the Indigo events log.

"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report_comms(values_dict: indigo.Dict = None, menu_item: str = ""):
    """
    Print information on the last successful communication

    :param indigo.Dict values_dict:
    :param str menu_item:
    :return:
    """
    dev_filter = values_dict['listOfDevices']
    if dev_filter == "all devices":
        dev_filter = ""

    # Get the data we need
    table = [
        (dev.id, dev.name, dev.lastSuccessfulComm) for dev in indigo.devices.iter(filter=dev_filter)
    ]

    # Filter returns zero devices of type selected.
    if len(table) == 0:
        table = [("No devices for the selected filter", " ", " ")]

    # Sort the data from newest to oldest
    # table = sorted(table, key=lambda (dev_id, name, comm): comm, reverse=True)
    table = sorted(table, key=lambda t: t[::-1], reverse=True)

    # Find the length of the longest device name
    length = 0
    for element in table:
        if len(element[1]) > length:
            length = len(element[1])

    # Output the result
    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
    # logging level.
    indigo.server.log(f"{' Device Last Successful Comm ':=^100}")
    indigo.server.log(f"{'ID':<14}{'Name':<{length + 1}} Last Comm Success")
    indigo.server.log('=' * 100)
    for element in table:
        indigo.server.log(f"{element[0]:<14}{element[1]:<{length}}  {element[2]}")
