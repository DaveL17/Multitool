"""
Title Placeholder

Body placeholder

:param indigo.ActionGroup action_group:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def modify(action_group):
    var_id = int(action_group.props['list_of_variables'])
    var = indigo.variables[var_id]
    expr = indigo.activePlugin.substitute(action_group.props['modifier'])

    try:
        answer = indigo.activePlugin.Eval.eval_expr(var.value + expr)
        indigo.variable.updateValue(var_id, f"{answer}")
        return_value = True

    except SyntaxError:
        LOGGER.critical("Error: ", exc_info=True)
        LOGGER.critical(f"Error modifying variable {var.name}.")
        return_value = False

    return return_value
