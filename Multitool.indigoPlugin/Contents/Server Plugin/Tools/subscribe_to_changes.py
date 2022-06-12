"""
Save "Subscribe to Changes" menu item configuration to plugin prefs for storage.

The subscribed_to_changes method is used to save the settings for the "Subscribe to
Changes" menu tool. We do this because there is no closedMenuConfigUi method similar to
closedDeviceConfigUi method. We must save the menu configuration settings to the plugin
configuration menu so that they're persistent.

:param indigo.Dict values_dict:
:param str type_id:
:return:
"""
import indigo
import logging

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def subscriber(values_dict):
    # If user changes subscription preference, set flag for plugin restart (see __init__)
    if indigo.activePlugin.pluginPrefs['enableSubscribeToChanges'] == values_dict['enableSubscribeToChanges']:
        restart_required = False
    else:
        restart_required = True

    # Save preferences to plugin config for storage
    indigo.activePlugin.pluginPrefs['enableSubscribeToChanges'] = values_dict['enableSubscribeToChanges']
    indigo.activePlugin.pluginPrefs['subscribedDevices'] = values_dict['subscribedDevices']

    if restart_required:
        indigo.server.log("Preparing to restart plugin...")
        indigo.activePlugin.sleep(2)

        indigo.activePlugin.restartPlugin(message="", isError=False)

    return True
