"""
Print the Indigo server's environment path variable to the Indigo Events log

the environment_path method outputs the value of the server computer's environment path variable to the Indigo events
log. This can help with trouble-shooting--for example, when an expected import statement fails.

:return:
"""

import logging
import sys
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_path(no_log: bool = False) -> None:
    """
    Print the Indigo server's environment path to the Indigo Events log

    :return:
    """
    # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
    # logging level.
    if not no_log:
        indigo.server.log(f"{' Current System Path ':{'='}^130}")
        for item in sys.path:
            indigo.server.log(item)
        indigo.server.log(f"\n{' Current System Path (Sorted) ':{'='}^130}")
        for item in sorted(sys.path):
            indigo.server.log(item)
