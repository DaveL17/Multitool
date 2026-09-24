"""
Utility Function to Output pip freeze report text.
"""

import logging
import indigo  # noqa
import subprocess
import sys

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(no_log: bool = False) -> bool:  # noqa
    """
    Prints pip freeze report to the Indigo Events Log

    :return:
    """
    # Use the running interpreter's own `-m pip` rather than a hard-coded path so this works
    # regardless of which Python version Indigo is actually running.
    result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True)
    header = "\n=====================================  pip freeze Output  =====================================\n"
    LOGGER.info(header + result.stdout)
    return True
