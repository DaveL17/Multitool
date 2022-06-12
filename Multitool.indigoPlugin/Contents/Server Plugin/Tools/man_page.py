"""
Title Placeholder

Body placeholder

:param class values_dict:
:param str type_id:
:return:
"""
import indigo
import logging
import subprocess

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def display_page(values_dict):
    cmd = values_dict['manToOpen']
    with subprocess.Popen(
            [f'man -t {cmd} | open -fa "Preview"'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
    ) as proc:
        result, err = proc.communicate()
        return_code = proc.returncode

    if len(err) > 0:
        LOGGER.exception(f"{err} [{return_code}]")

    return True
