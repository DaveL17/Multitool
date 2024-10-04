"""
Print a list of serial ports to the Indigo events log

The get_serial_ports method prints a list of available serial ports to the Indigo events log.
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_ports(values_dict: indigo.Dict = None, no_log: bool = False) -> bool:
    """
    Print a list of available serial ports to the Indigo events log.

    :param indigo.Dict values_dict:
    :param bool no_log:  If True, no output is logged.
    :return:
    """
    # ========================= Filter Bluetooth Devices ==========================
    if values_dict.get('ignoreBluetooth', False):
        port_filter = "indigo.ignoreBluetooth"
    else:
        port_filter = ""

    if not no_log:
        # ============================= Print the Report ==============================
        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        indigo.server.log(f"{' Current Serial Ports ':=^80}")

        for key, value in indigo.server.getSerialPorts(filter=f"{port_filter}").items():
            indigo.server.log(f"{key:40} {value}")

        return True
