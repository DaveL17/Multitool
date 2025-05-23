"""
Modifies a variable value based on a user-supplied formula
"""
import logging
import datetime as dt
import operator
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def modify(action_group: indigo.actionGroup = None) -> bool:
    """
    Modifies a variable time value based on a user-supplied formula

    :param indigo.actionGroup action_group:
    :return:
    """
    var_id = int(action_group.props['list_of_variables'])
    var = indigo.variables[var_id]
    expr = action_group.props['modifier']
    seconds = indigo.activePlugin.substitute(action_group.props['seconds'])
    minutes = indigo.activePlugin.substitute(action_group.props['minutes'])
    hours = indigo.activePlugin.substitute(action_group.props['hours'])
    days = indigo.activePlugin.substitute(action_group.props['days'])
    ops = {"add": operator.add, "subtract": operator.sub}

    try:
        my_date = dt.datetime.strptime(var.value, "%Y-%m-%d %H:%M:%S.%f")
        delta = dt.timedelta(
            days=float(days),
            hours=float(hours),
            minutes=float(minutes),
            seconds=float(seconds)
        )
        d_s = ops[expr](my_date, delta)
        indigo.variable.updateValue(var_id, f"{d_s}")
        return True

    except ValueError:
        LOGGER.critical("Error: ", exc_info=True)
        LOGGER.critical(f"Error modifying variable %s." % var.name)
        return False
