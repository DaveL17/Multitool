"""
Print a list of serial ports to the Indigo events log

The get_serial_ports method prints a list of available serial ports to the Indigo events log.
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_ports(values_dict:indigo.Dict=None):
    """
    Print a list of available serial ports to the Indigo events log.

    :param indigo.Dict values_dict:
    :return:
    """
    # ========================= Filter Bluetooth Devices ==========================
    if values_dict.get('ignoreBluetooth', False):
        port_filter = "indigo.ignoreBluetooth"
    else:
        port_filter = ""

    # ============================= Print the Report ==============================
    indigo.server.log(f"{' Current Serial Ports ':=^80}")

    for key, value in indigo.server.getSerialPorts(filter=f"{port_filter}").items():
        indigo.server.log(f"{key:40} {value}")

    return True
