"""
Utility Function to Output pip freeze report text.
"""

import logging
import indigo  # noqa
import subprocess

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(no_log: bool = False) -> bool:  # noqa
    """
    Prints pip freeze report to the Indigo Events Log

    :return:
    """
    result = subprocess.run(['/Library/Frameworks/Python.framework/Versions/3.13/bin/pip3', 'freeze'], capture_output=True, text=True)
    header = "\n=====================================  pip freeze Output  =====================================\n"
    LOGGER.info(header + result.stdout)
    return True
