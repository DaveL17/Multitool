"""
Prints information about the Indigo environment to the events log

The about_indigo method prints select Indigo environment information to the Indigo events log. It can be a useful tool
to get a user to quickly print relevant environment information for troubleshooting.  We write to `indigo.server.log`
to ensure that the output is visible regardless of the plugin's current logging level.
"""

import logging
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def report(no_log: bool = False) -> None:
    """
    Prints information about the Indigo environment to the Indigo Events Log

    :return:
    """
    lat_long = indigo.server.getLatitudeAndLongitude()
    latitude = lat_long[0]
    longitude = lat_long[1]

    if not no_log:
        indigo.server.log(f"{' Indigo Status Information ':{'='}^130}")
        indigo.server.log(f"Server Version: {indigo.server.version}")
        indigo.server.log(f"API Version: {indigo.server.apiVersion}")
        indigo.server.log(f"Server IP Address: {indigo.server.address}")
        indigo.server.log(f"Install Path: {indigo.server.getInstallFolderPath()}")
        indigo.server.log(f"Database: {indigo.server.getDbFilePath()}/{indigo.server.getDbName()}")
        indigo.server.log(f"Port Number: {indigo.server.portNum}")
        indigo.server.log(f"Latitude and Longitude: {latitude}/{longitude}")

        if indigo.server.connectionGood:
            indigo.server.log("Connection Good.")
        else:
            indigo.server.log("Connection Bad.")
