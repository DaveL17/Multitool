"""
Title Placeholder

Body placeholder

:return:
"""
import logging
try:
    import indigo
except ImportError:
    pass

LOGGER = logging.getLogger()


def __init__():
    pass


def show_inventory():
    """
    Build a complete inventory of Indigo objects and output it to the Indigo Events log

    :return:
    """
    # ============================== Build Inventory ==============================
    inventory = {
        'Action Groups': [],
        'Control Pages': [],
        'Devices': [],
        'Schedules': [],
        'Triggers': [],
        'Variables': []
    }

    for action in indigo.actionGroups.iter():
        inventory['Action Groups'].append(
            (
                action.id,
                action.name,
                action.folderId,
                indigo.actionGroups.folders.getName(action.folderId)
            )
        )

    for page in indigo.controlPages.iter():
        inventory['Control Pages'].append(
            (
                page.id,
                page.name,
                page.folderId,
                indigo.controlPages.folders.getName(page.folderId)
            )
        )

    for dev in indigo.devices.iter():
        inventory['Devices'].append(
            (
                dev.id,
                dev.name,
                dev.folderId,
                indigo.devices.folders.getName(dev.folderId)
            )
        )

    for schedule in indigo.schedules.iter():
        inventory['Schedules'].append(
            (
                schedule.id,
                schedule.name,
                schedule.folderId,
                indigo.schedules.folders.getName(schedule.folderId)
            )
        )

    for trigger in indigo.triggers.iter():
        inventory['Triggers'].append(
            (
                trigger.id,
                trigger.name,
                trigger.folderId,
                indigo.triggers.folders.getName(trigger.folderId)
            )
        )

    for var in indigo.variables.iter():
        inventory['Variables'].append(
            (
                var.id,
                var.name,
                var.folderId,
                indigo.variables.folders.getName(var.folderId)
            )
        )

    # ====================== Generate Custom Table Settings =======================
    col_0 = []
    col_1 = []
    col_2 = []
    col_3 = []

    for key in inventory.keys():
        col_0 += [item[0] for item in inventory[key]]
        col_1 += [item[1] for item in inventory[key]]
        col_2 += [item[2] for item in inventory[key]]
        col_3 += [item[3] for item in inventory[key]]

    col0 = max([len(f"{item}") for item in col_0]) + 2
    col1 = max([len(f"{item}") for item in col_1]) + 2
    col2 = max([len(f"{item}") for item in col_2]) + 2
    col3 = max([len(f"{item}") for item in col_3]) + 2

    table_width = sum([col0, col1, col2, col3])

    # ============================= Output the Table ==============================
    for object_type in sorted(inventory):
        header = f" {object_type} "
        indigo.server.log(f"{header:{'='}^{table_width}}")

        indigo.server.log(
            f"{'ID':{col0}}{'Name':{col1}}{'Folder ID':{col2}}{'Folder Name':{col3}}"
        )
        indigo.server.log("=" * table_width)

        for element in inventory[object_type]:
            indigo.server.log(
                f"{element[0]:<{col0}}"
                f"{element[1]:<{col1}}"
                f"{element[2]:<{col2}}"
                f"{element[3]:<{col3}}"
            )

    indigo.server.log(f"{' Summary ':{'='}^{table_width}}")

    for object_type in sorted(inventory):
        indigo.server.log(f"{object_type:15}{len(inventory[object_type])}")
