"""
Traverse the Indigo database and find objects with embedded scripts

This tool is only available to users of Indigo 2024.1.0 and later.
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")
SPACER = f"{'':35}"
obj_list = []  # Container for objects with embedded scripts [(obj.id, obj.name), ...]


def __init__():
    pass


def sort_obj_list(ob_list: list) -> str:
    """
    Sort the list of objects by their object name

    :param ob_list: list of objects
    """
    result = ""
    new_ob_list = (sorted(ob_list, key=lambda item: item[1]))
    for obj in new_ob_list:
        result += f"{SPACER}{obj[0]:<10} - {obj[1]} [ {obj[2]} ]\n"
    obj_list.clear()
    return result


def build_report(header: str) -> str:
    """
    Add payload objects to the report

    :param header: header of the report
    """
    # Note that we don't want to combine "duplicates" here because we are going to be showing the full path which might
    # be quite long.
    report = f"\n{SPACER}{' ' + header + ' ':=^60}\n"
    report += sort_obj_list(obj_list)  # put the objects in alpha order by name
    return report


# Note that there is no search criteria needed as the script is not going to search linked scripts.
def make_report(values_dict: indigo.Dict, no_log: bool = False):
    """
    Traverse the database and find objects with linked scripts and publish report to events log

    We intentionally split the `rawServerRequests` apart because some users have massive databases and even this
    small separation may give the server a bit of a break. We evaluate each object type separately because there can be
    nuanced differences in the database XML and the format of the XML could change in the future.

    :param values_dict:
    :param bool no_log: If True, no output is logged.
    """
    result = "Indigo Objects with Linked Scripts"

    # Check server version compatability
    if not indigo.server.version >= "2024.1.0":
        LOGGER.warning("The linked scripts tool requires Indigo 2024.1 or later.")
        return False

    # ====================== Action Groups =======================
    for action_group in indigo.rawServerRequest("GetActionGroupList"):
        for step in action_group['ActionSteps']:
            if step.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                obj_list.append((action_group['ID'], action_group['Name'], step['ScriptLinkURL']))
    if obj_list:
        result += build_report("Action Groups")  # Only if there are results to return

    # ====================== Control Pages =======================
    for page in indigo.rawServerRequest("GetControlPageList"):
        for elem in page['PageElemList']:
            for action in elem['ActionGroup']['ActionSteps']:
                if action.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                    obj_list.append((page['ID'], page['Name'], action['ScriptLinkURL']))
    if obj_list:
        result += build_report("Control Pages")  # Only if there are results to return

    # ======================== Schedules =========================
    for schedule in indigo.rawServerRequest("GetEventScheduleList"):
        for action in schedule['ActionGroup']['ActionSteps']:
            if action.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                obj_list.append((schedule['ID'], schedule['Name'], action['ScriptLinkURL']))
    if obj_list:
        result += build_report("Schedules")  # Only if there are results to return

    # ========================= Triggers =========================
    for trigger in indigo.rawServerRequest("GetEventTriggerList"):
        for event in trigger['ActionGroup']['ActionSteps']:
            if event.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                obj_list.append((trigger['ID'], trigger['Name'], event['ScriptLinkURL']))
    if obj_list:
        result += build_report("Triggers")  # Only if there are results to return

    if not no_log:
        indigo.server.log(result)
    return True, values_dict
