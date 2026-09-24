"""
Traverse the Indigo database and find objects with embedded scripts

This tool is only available to users of Indigo 2024.1.0 and later.
"""
import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")
SPACER = f"{'':35}"


def __init__():
    pass


def _version_at_least(version: str, minimum: str) -> bool:
    """
    Compare dotted version strings numerically rather than lexicographically.

    Plain string comparison gives the wrong answer once any component reaches two
    digits (e.g. "2024.9.0" > "2024.10.0" under string ordering, which is backwards).

    :param str version: Version string to check (e.g. indigo.server.version).
    :param str minimum: Minimum required version string.
    :return: True if version >= minimum.
    """
    def _parts(v: str) -> tuple:
        return tuple(int(p) for p in v.split('.'))

    return _parts(version) >= _parts(minimum)


def sort_obj_list(ob_list: list) -> str:
    """
    Sort the list of objects by their object name

    :param ob_list: list of objects
    """
    result = ""
    new_ob_list = (sorted(ob_list, key=lambda item: item[1]))
    for obj in new_ob_list:
        result += f"{SPACER}{obj[0]:<10} - {obj[1]} [ {obj[2]} ]\n"
    return result


def build_report(header: str, obj_list: list) -> str:
    """
    Add payload objects to the report

    :param header: header of the report
    :param list obj_list: objects with linked scripts found in this section [(obj.id, obj.name, url), ...]
    """
    # Note that we don't want to combine "duplicates" here because we are going to be showing the full path which might
    # be quite long.
    report = f"\n{SPACER}{' ' + header + ' ':=^100}\n"
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
    result = f"{' Indigo Objects with Linked Scripts ':=^100}"

    # Check server version compatability
    if not _version_at_least(indigo.server.version, "2024.1.0"):
        LOGGER.warning("The linked scripts tool requires Indigo 2024.1 or later.")
        return False

    # ====================== Action Groups =======================
    obj_list = []
    for action_group in indigo.rawServerRequest("GetActionGroupList"):
        for step in action_group['ActionSteps']:
            if step.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                obj_list.append((action_group['ID'], action_group['Name'], step['ScriptLinkURL']))
    if obj_list:
        result += build_report("Action Groups", obj_list)  # Only if there are results to return

    # ====================== Control Pages =======================
    obj_list = []
    for page in indigo.rawServerRequest("GetControlPageList"):
        for elem in page['PageElemList']:
            for action in elem['ActionGroup']['ActionSteps']:
                if action.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                    obj_list.append((page['ID'], page['Name'], action['ScriptLinkURL']))
    if obj_list:
        result += build_report("Control Pages", obj_list)  # Only if there are results to return

    # ======================== Schedules =========================
    obj_list = []
    for schedule in indigo.rawServerRequest("GetEventScheduleList"):
        for action in schedule['ActionGroup']['ActionSteps']:
            if action.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                obj_list.append((schedule['ID'], schedule['Name'], action['ScriptLinkURL']))
    if obj_list:
        result += build_report("Schedules", obj_list)  # Only if there are results to return

    # ========================= Triggers =========================
    obj_list = []
    for trigger in indigo.rawServerRequest("GetEventTriggerList"):
        for event in trigger['ActionGroup']['ActionSteps']:
            if event.get('ScriptLinkURL', "no file chosen") != "no file chosen":
                obj_list.append((trigger['ID'], trigger['Name'], event['ScriptLinkURL']))
    if obj_list:
        result += build_report("Triggers", obj_list)  # Only if there are results to return

    if not no_log:
        result += f"\n{SPACER}" + '=' * 100
        indigo.server.log(result)
    return True, values_dict
