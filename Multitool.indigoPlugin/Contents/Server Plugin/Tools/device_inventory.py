"""
Print an inventory of Indigo devices to the Indigo events log

The device_inventory method prints an inventory of all Indigo devices to the Indigo events log.
"""
import datetime as dt
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def get_inventory(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> dict:
    """
    Print an inventory of devices to the Indigo Events log

    :param indigo.Dict values_dict:
    :param str type_id:
    :param bool no_log: If True, no output is logged.
    :return:
    """
    LOGGER.debug("Call to device_inventory")

    filter_item = ""
    inventory = []

    if values_dict['typeOfThing'] not in ('Other', 'pickone'):
        filter_item = values_dict['typeOfThing']
        inventory = [
            [dev.id, dev.address, dev.name, dev.lastChanged, dev.enabled] for dev
            in indigo.devices.iter(filter=filter_item)
        ]

    elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
        filter_item = values_dict['customThing']
        inventory = [
            [dev.id, dev.address, dev.name, dev.lastChanged, dev.enabled] for dev
            in indigo.devices.iter(filter=filter_item)
        ]

    if len(inventory) > 0:
        # ====================== Generate Custom Table Settings =======================
        x_0 = max(len(f"{thing[0]}") for thing in inventory) + 2
        x_1 = max(len(f"{thing[1]}") for thing in inventory) + 2
        x_2 = max(len(f"{thing[2]}") for thing in inventory) + 2
        x_3 = max(len(f"{thing[3]}") for thing in inventory)
        x_4 = max(len(f"{thing[4]}") for thing in inventory)
        table_width = sum((x_0, x_1, x_2, x_3, x_4)) + 6

        if not no_log:
            # ============================= Output the Header =============================
            # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
            # logging level.
            indigo.server.log(f"{f' Inventory of {filter_item} Devices ':=^{table_width}}")
            indigo.server.log(
                f"{'ID':<{x_0}} {'Addr':<{x_1}} "
                f"{'Name':<{x_2}} "
                f"{'Last Changed':<{x_3}} "
                f"{'Enabled':<3}"
            )
            indigo.server.log("=" * table_width)

            # ============================= Output the Table ==============================
            checkmark = "\u2714"
            for thing in inventory:
                indigo.server.log(
                    f"{thing[0]:<{x_0}} "
                    f"{f'[{thing[1]}]':<{x_1}} "
                    f"{thing[2]:<{x_2}} "
                    f"{dt.datetime.strftime(thing[3], '%Y-%m-%d %H:%M:%S'):<{x_3}} "
                    f"[ {checkmark if thing[4] == 1 else '':^3} ]"
                )
    else:
        if not no_log:
            if values_dict['typeOfThing'] not in ('Other', 'pickone'):
                indigo.server.log(f"No {values_dict['typeOfThing']} devices found.")
            elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
                indigo.server.log(f"No {values_dict['customThing']} devices found.")

    return values_dict
