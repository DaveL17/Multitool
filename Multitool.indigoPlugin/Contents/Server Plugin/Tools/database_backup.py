"""
Creates a verified backup copy of the live Indigo database.

The backup method duplicates the current Indigo database to a temporary location, verifies the duplicate is stable
by reading it twice and comparing the results, saves the verified copy to a user-specified folder under a dated
filename, verifies the saved file against the in-memory duplicate, and finally prunes old backups beyond the
configured retention count. The live database file is only ever opened for reading (via `shutil.copy2`) and is never
modified.
"""
import datetime as dt
import glob
import logging
import os
import shutil
import tempfile
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


def backup(action_group: indigo.actionGroup = None) -> bool:
    """
    Create a verified backup of the live Indigo database.

    :param indigo.actionGroup action_group: Indigo action group containing the backup_folder and retain_count props.
    :return: True on a fully verified, successful backup; False otherwise.
    """
    try:
        backup_folder = indigo.activePlugin.substitute(action_group.props['backup_folder']).strip()
        retain_count  = int(action_group.props['retain_count'])

        if not backup_folder:
            LOGGER.critical("Database backup aborted: no backup folder specified.")
            return False

        if retain_count <= 0:
            LOGGER.critical("Database backup aborted: retain_count must be a whole number greater than zero.")
            return False

        os.makedirs(backup_folder, exist_ok=True)

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
            with open(target_path, 'wb') as outfile:
                outfile.write(first_read)

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

        _prune_old_backups(backup_folder, basename, ext, retain_count)

        return True

    except Exception:
        LOGGER.critical("Error creating database backup: ", exc_info=True)
        return False
