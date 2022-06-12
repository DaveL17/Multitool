"""
Print a list of serial ports to the Indigo events log

The get_serial_ports method prints a list of available serial ports to the Indigo events
log.

:param indigo.Dict values_dict:
:param str type_id:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_ports(values_dict):
    # ========================= Filter Bluetooth Devices ==========================
    if values_dict.get('ignoreBluetooth', False):
        port_filter = "indigo.ignoreBluetooth"
    else:
        port_filter = ""

    # ============================= Print the Report ==============================
    indigo.server.log(f"{' Current Serial Ports ':=^80}")

    for k, v in indigo.server.getSerialPorts(filter=f"{port_filter}").items():
        indigo.server.log(f"{k:40} {v}")

    return True
