"""
Create an inventory of error messages appearing in the Indigo Logs.

The error_inventory method will scan log files and parse out any log lines than contain the
term 'error'. It is agnostic about whether the log line is an actual error or a debug
statement that contains the term error.

:param indigo.Dict values_dict:
:param int type_id:
:return:
"""
import indigo
import logging
import os

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_inventory(values_dict):
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
    with open(full_path, 'w', encoding='utf-8') as outfile:
        for root, sub, files in os.walk(log_folder):
            for filename in files:
                # if filename.endswith((".log", ".txt")) and filename != 'error_inventory.txt':
                if filename.endswith((".log", ".txt")) \
                        and not filename.startswith('Multitool Plugin Error Inventory'):
                    with open(os.path.join(root, filename), "r", encoding="utf-8") as infile:
                        log_file = infile.read()

                        for line in log_file.split('\n'):
                            if any(item in line for item in check_list):
                                outfile.write(f"{root + filename:<130}{line}\n")

    indigo.server.log(f"Error message inventory saved to: {full_path}")
    return True
