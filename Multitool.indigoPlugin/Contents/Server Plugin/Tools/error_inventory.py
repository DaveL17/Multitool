"""
Create an inventory of error messages appearing in the Indigo Logs.

The error_inventory method will scan log files and parse out any log lines than contain the term 'error'. It is
agnostic about whether the log line is an actual error or a debug statement that contains the term error.
"""
import logging
import os
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_inventory(values_dict: indigo.Dict = None, no_log: bool = False) -> bool:
    """
    Print an inventory of error messages to the Indigo Events log

    :param indigo.Dict values_dict:
    :param bool no_log: If True, no output is logged.
    :return:
    """
    check_list = (' Err ', ' err ', 'Error', 'error')
    if values_dict.get('error_level', 'err') == 'err_warn':
        check_list += ('Warning', 'warning')
    log_folder = f"{indigo.server.getLogsFolderPath()}/"

    # ========================= Create a Unique Filename ==========================
    i = 1
    while os.path.exists(f"{log_folder}Multitool Plugin Error Inventory {i}.txt"):
        i += 1

    full_path = f"{log_folder}Multitool Plugin Error Inventory {i}.txt"

    # ============================= Iterate Log Files =============================
    log_lines = []

    for root, sub, files in os.walk(log_folder):
        for filename in files:
            if filename.endswith((".log", ".txt")) and not filename.startswith('Multitool Plugin Error Inventory'):
                with open(os.path.join(root, filename), "r", encoding="utf-8") as infile:
                    log_file = infile.read()

                    for line in log_file.split('\n'):
                        if any(item in line for item in check_list):
                            log_lines.append(f"{filename:<26}{line}\n")

    # Write to outfile only if no_log is False
    if not no_log:
        with open(full_path, 'w', encoding='utf-8') as outfile:
            outfile.writelines(log_lines)
            # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
            # logging level.
            indigo.server.log(f"Error message inventory saved to: {full_path}")

    return True
