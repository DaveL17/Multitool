"""
Traverse the Indigo database and find objects with embedded scripts
"""
from collections import defaultdict
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")
SPACER = f"{'':35}"


def __init__():
    pass


def sort_obj_list(ob_list: list) -> str:
    """
    Sort the list of objects by their object name

    :param list ob_list: list of objects
    """
    result = ""
    new_ob_list = sorted(ob_list, key=lambda item: item[1])
    for obj in new_ob_list:
        result += f"{SPACER}{obj[0]:<10} - {obj[1]}\n"
    return result


def build_report(header: str, obj_list: list) -> str:
    """
    Add payload objects to the report

    :param str header: header string
    :param list obj_list: objects with embedded scripts found in this section [(obj.id, obj.name), ...]
    """
    report = f"\n{SPACER}{' ' + header + ' ':=^60}\n"
    count_dict = defaultdict(int)

    # Count occurrences to account for objects with multiple embedded scripts
    for item in obj_list:
        count_dict[item] += 1

    # Create the new list with the number of scripts accounted for
    result = []
    for item, count in count_dict.items():
        if count > 1:
            result.append((item[0], f"{item[1]} ({count} scripts)"))
        else:
            result.append(item)

    if len(result) > 0:
        report += sort_obj_list(result)  # put the objects in alpha order by name
    else:
        report += "No objects found."
    return report


def make_report(values_dict: indigo.Dict, no_log: bool = False):
    """
    Traverse the database and find objects with embedded scripts and publish report to events log

    We intentionally split the `rawServerRequests` apart because some users have massive databases and even this
    small separation may give the server a bit of a break. We evaluate each object type separately because there can be
    nuanced differences in the database XML and the format of the XML could change in the future.

    :param dict values_dict:
    :param bool no_log: If True, no output is logged.
    """
    error_msg_dict = indigo.Dict()
    try:
        if not isinstance(values_dict['search_string'], str):
            raise TypeError
        search_string: str = values_dict['search_string']  # For finding embedded scripts containing the string
    except TypeError:
        error_msg_dict['search_string'] = "The search term must be a string"
        return False, values_dict, error_msg_dict
    result = f"{' Indigo Objects with Embedded Scripts ':=^60}"
    result += f"\n{SPACER}Search Filter: [ {search_string or 'None'} ]"

    # ====================== Action Groups =======================
    obj_list = []
    for action_group in indigo.rawServerRequest("GetActionGroupList"):
        for step in action_group['ActionSteps']:
            if step.get('ScriptSource', None):
                if search_string in step['ScriptSource']:
                    obj_list.append((action_group['ID'], action_group['Name']))
    if obj_list:
        result += build_report("Action Groups", obj_list)  # Only if there are results to return

    # ====================== Control Pages =======================
    obj_list = []
    for page in indigo.rawServerRequest("GetControlPageList"):
        for elem in page['PageElemList']:
            for action in elem['ActionGroup']['ActionSteps']:
                if action.get('ScriptSource', None):
                    if search_string in action['ScriptSource']:
                        obj_list.append((page['ID'], page['Name']))
    if obj_list:
        result += build_report("Control Pages", obj_list)  # Only if there are results to return

    # ======================== Schedules =========================
    obj_list = []
    for schedule in indigo.rawServerRequest("GetEventScheduleList"):
        for action in schedule['ActionGroup']['ActionSteps']:
            if action.get('ScriptSource', None):
                if search_string in action['ScriptSource']:
                    obj_list.append((schedule['ID'], schedule['Name']))
    if obj_list:
        result += build_report("Schedules", obj_list)  # Only if there are results to return

    # ========================= Triggers =========================
    obj_list = []
    for trigger in indigo.rawServerRequest("GetEventTriggerList"):
        for event in trigger['ActionGroup']['ActionSteps']:
            if event.get('ScriptSource', None):
                if search_string in event['ScriptSource']:
                    obj_list.append((trigger['ID'], trigger['Name']))
    if obj_list:
        result += build_report("Triggers", obj_list)  # Only if there are results to return

    if not no_log:
        result += f"{SPACER}" + "=" * 60 + "\n"
        indigo.server.log(result)
    return True, values_dict
