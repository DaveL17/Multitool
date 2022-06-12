"""
Print a list of installed plugins to the Indigo events log

The installed_plugins method will print a list of installed plugins to the Indigo events
log along with the plugin's bundle identifier. In instances where the plugin is disabled,
[Disabled] will be appended to the log line.

:return:
"""
import indigo
import logging
import plistlib
import os

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def get_list():

    plugin_name_list = []
    indigo_install_path = indigo.server.getInstallFolderPath()

    for plugin_folder in ('Plugins', 'Plugins (Disabled)'):
        plugins_list = os.listdir(indigo_install_path + '/' + plugin_folder)

        for plugin in plugins_list:

            # Check for Indigo Plugins and exclude 'system' plugins
            if (plugin.lower().endswith('.indigoplugin')) and (not plugin[0:1] == '.'):

                # retrieve plugin Info.plist file
                with open(
                        f"{indigo_install_path}/{plugin_folder}/{plugin}"
                        f"/Contents/Info.plist", 'rb') as p_list:
                    pl = plistlib.load(p_list)

                cf_bundle_identifier = pl["CFBundleIdentifier"]

                # Don't include self (i.e. this plugin) in the plugin list
                cf_bundle_display_name = pl["CFBundleDisplayName"]

                # if disabled plugins folder, append 'Disabled' to name
                if plugin_folder == 'Plugins (Disabled)':
                    cf_bundle_display_name += ' [Disabled]'

                plugin_name_list.append(f"{cf_bundle_display_name:45}{cf_bundle_identifier}")

    indigo.server.log(f"{' Installed Plugins ':{'='}^130}")

    for thing in plugin_name_list:
        indigo.server.log(f'{thing}')

    indigo.server.log(f"{' Code Credit: Autolog ':{'='}^130}")
