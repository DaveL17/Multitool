"""
Print an inventory of Indigo devices to the Indigo events log

The device_inventory method prints an inventory of all Indigo devices to the Indigo events
log.
"""
import datetime as dt
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def get_inventory(values_dict, type_id):
    """
    :param indigo.Dict values_dict:
    :param str type_id:
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
        x0 = max([len(f"{thing[0]}") for thing in inventory]) + 2
        x1 = max([len(f"{thing[1]}") for thing in inventory]) + 2
        x2 = max([len(f"{thing[2]}") for thing in inventory]) + 2
        x3 = max([len(f"{thing[3]}") for thing in inventory])
        x4 = max([len(f"{thing[4]}") for thing in inventory])
        table_width = sum((x0, x1, x2, x3, x4)) + 6

        # ============================= Output the Header =============================
        indigo.server.log(f"{f' Inventory of {filter_item} Devices ':=^{table_width}}")
        indigo.server.log(
            f"{'ID':<{x0}} {'Addr':<{x1}} "
            f"{'Name':<{x2}} "
            f"{'Last Changed':<{x3}} "
            f"{'Enabled':<3}"
        )
        indigo.server.log("=" * table_width)

        # ============================= Output the Table ==============================
        for thing in inventory:
            indigo.server.log(
                f"{thing[0]:<{x0}} "
                f"{f'[{thing[1]}]':<{x1}} "
                f"{thing[2]:<{x2}} "
                f"{dt.datetime.strftime(thing[3], '%Y-%m-%d %H:%M:%S'):<{x3}} "
                f"[ {thing[4]:^3} ]"
            )
    else:
        if values_dict['typeOfThing'] not in ('Other', 'pickone'):
            indigo.server.log(f"No {values_dict['typeOfThing']} devices found.")
        elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
            indigo.server.log(f"No {values_dict['customThing']} devices found.")

    return values_dict
