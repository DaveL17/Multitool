"""
Creates a verified backup copy of the live Indigo database.

The backup function duplicates the current Indigo database to a temporary location, verifies the duplicate is
stable by reading it twice and comparing the results, saves the verified copy to a folder under a dated filename,
verifies the saved file against the in-memory duplicate, and (optionally) prunes old backups beyond a retention
count. The live database file is only ever opened for reading (via `shutil.copy2`) and is never modified.

backup_from_action and backup_to_desktop are the two entry points used by the plugin's action and menu item,
respectively; both call the shared backup function.
"""
import datetime as dt
import glob
import logging
import os
import shutil
import tempfile
from typing import Optional
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def _build_target_path(backup_folder: str, basename: str, ext: str) -> str:
    """
    Build a unique, dated backup file path within backup_folder.

    Returns a path of the form "<basename> backup <YYYY MM DD><ext>", or, if that name already exists,
    "<basename> backup <YYYY MM DD> (NN)<ext>" with NN incrementing until a free name is found.

    :param str backup_folder: Destination folder for the backup file.
    :param str basename: Original database filename without its extension.
    :param str ext: Original database file extension (including the leading dot).
    :return: A full, currently-unused file path.
    """
    date_str = dt.datetime.now().strftime("%Y %m %d")
    candidate = os.path.join(backup_folder, f"{basename} backup {date_str}{ext}")

    sequence = 1
    while os.path.exists(candidate):
        candidate = os.path.join(backup_folder, f"{basename} backup {date_str} ({sequence:02d}){ext}")
        sequence += 1

    return candidate


def _prune_old_backups(backup_folder: str, basename: str, ext: str, retain_count: int) -> None:
    """
    Delete the oldest backup files for this database beyond retain_count.

    :param str backup_folder: Folder containing the backup files.
    :param str basename: Original database filename without its extension.
    :param str ext: Original database file extension (including the leading dot).
    :param int retain_count: Number of backup files to keep.
    :return: None
    """
    pattern = os.path.join(backup_folder, f"{basename} backup *{ext}")
    matches = sorted(glob.glob(pattern), key=os.path.getmtime)

    for stale_path in matches[:-retain_count] if len(matches) > retain_count else []:
        try:
            os.remove(stale_path)
            LOGGER.debug("Removed old database backup: %s", stale_path)
        except OSError:
            LOGGER.critical("Error removing old database backup: %s", stale_path, exc_info=True)


def backup(backup_folder: str, retain_count: Optional[int] = None) -> bool:
    """
    Create a verified backup of the live Indigo database.

    :param str backup_folder: Destination folder to save the backup to (created automatically if it doesn't exist).
    :param Optional[int] retain_count: Number of backup files to keep for this database. Must be a whole number
        greater than zero. If None, old backups are never pruned.
    :return: True on a fully verified, successful backup; False otherwise.
    """
    try:
        backup_folder = backup_folder.strip()

        if not backup_folder:
            LOGGER.critical("Database backup aborted: no backup folder specified.")
            return False

        if retain_count is not None and retain_count <= 0:
            LOGGER.critical("Database backup aborted: retain_count must be a whole number greater than zero.")
            return False

        try:
            os.makedirs(backup_folder, exist_ok=True)
        except OSError as ex:
            LOGGER.critical("Database backup aborted: could not create backup folder '%s' (%s).", backup_folder, ex)
            return False

        # The original database is only ever read from -- never opened for writing.
        original_db_path = indigo.server.getDbFilePath()
        original_filename = os.path.basename(original_db_path)
        basename, ext = os.path.splitext(original_filename)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db_path = os.path.join(temp_dir, original_filename)

            # ================================ Duplicate ===============================
            shutil.copy2(original_db_path, temp_db_path)

            # ============================ Load and Verify =============================
            with open(temp_db_path, 'rb') as infile:
                first_read = infile.read()
            with open(temp_db_path, 'rb') as infile:
                second_read = infile.read()

            if first_read != second_read:
                LOGGER.critical("Database backup aborted: duplicate database could not be read consistently.")
                return False

            # ================================ Save Copy ================================
            target_path = _build_target_path(backup_folder, basename, ext)
            try:
                with open(target_path, 'wb') as outfile:
                    outfile.write(first_read)
            except OSError as ex:
                LOGGER.critical("Database backup aborted: could not write backup file '%s' (%s).", target_path, ex)
                return False

            # ============================== Verify Saved File ==============================
            with open(target_path, 'rb') as infile:
                saved_read = infile.read()

            if saved_read != first_read:
                LOGGER.critical(
                    "Database backup failed integrity check. Saved file does not match the verified duplicate: %s",
                    target_path
                )
                return False

        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        indigo.server.log(f"Database backup saved to: {target_path}")

        if retain_count is not None:
            _prune_old_backups(backup_folder, basename, ext, retain_count)

        return True

    except Exception:
        LOGGER.critical("Error creating database backup: ", exc_info=True)
        return False


def backup_from_action(action_group: indigo.actionGroup = None) -> bool:
    """
    Create a verified backup of the live Indigo database using an action's configured folder and retention count.

    :param indigo.actionGroup action_group: Indigo action group containing the backup_folder and retain_count props.
    :return: True on a fully verified, successful backup; False otherwise.
    """
    backup_folder = indigo.activePlugin.substitute(action_group.props['backup_folder']).strip()
    try:
        retain_count = int(action_group.props['retain_count'])
    except (TypeError, ValueError):
        LOGGER.critical("Database backup aborted: retain_count must be a whole number greater than zero.")
        return False
    return backup(backup_folder, retain_count)


def backup_to_desktop() -> bool:
    """
    Create a verified backup of the live Indigo database on the user's desktop, with no retention pruning.

    Intended for developers who want to create ad hoc backups (e.g. during a development cycle) without needing
    older desktop backups automatically cleaned up.

    :return: True on a fully verified, successful backup; False otherwise.
    """
    desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
    return backup(desktop_folder, retain_count=None)
