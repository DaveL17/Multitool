# noqa pylint: disable=too-many-lines, line-too-long, invalid-name, unused-argument, redefined-builtin, broad-except, fixme

"""
Multitool Indigo Plugin
author: DaveL17

THe Multitool plugin provides a set of tools for use in using Indigo and for use when developing
plugins for Indigo.
"""

# =================================== TO DO ===================================
# TODO: Add a config menu and filter so users can list a subset of devices, and be able to
#       generate multiple reports without revisiting the tool. (Device last successful comm.)

# ================================== IMPORTS ==================================
# Built-in modules
import datetime as dt
import inspect
import logging
import operator
import os
import plistlib
import subprocess
import sys

# Third-party modules
try:
    import indigo  # noqa
    import pydevd
except ImportError as error:
    pass

# My modules
import DLFramework.DLFramework as Dave  # noqa
from constants import *  # noqa
from plugin_defaults import kDefaultPluginPrefs  # noqa

# =================================== HEADER ==================================
__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'Multitool Plugin for Indigo Home Control'
__version__   = '2022.1.1'


# =============================================================================
class Plugin(indigo.PluginBase):
    """
    Standard Indigo Plugin Class

    :param indigo.PluginBase:
    """
    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        """
        Plugin initialization

        :param str plugin_id:
        :param str plugin_display_name:
        :param str plugin_version:
        :param indigo.Dict plugin_prefs:
        """
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)

        # ============================ Instance Attributes =============================
        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False

        # =============================== Debug Logging ================================
        log_format = '%(asctime)s.%(msecs)03d\t%(levelname)-10s\t%(name)s.%(funcName)-28s %(msg)s'
        self.debug_level = int(self.pluginPrefs.get('showDebugLevel', '30'))
        self.plugin_file_handler.setFormatter(
            logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        )
        self.indigo_log_handler.setLevel(self.debug_level)

        # ====================== Initialize DLFramework =======================
        self.Fogbert = Dave.Fogbert(self)
        self.Eval    = Dave.evalExpr(self)
        # Log pluginEnvironment information when plugin is first started
        self.Fogbert.pluginEnvironment()

        # ============================= Remote Debugging ==============================
        try:
            pydevd.settrace(
                'localhost',
                port=5678,
                stdoutToServer=True,
                stderrToServer=True,
                suspend=False
            )
        except:
            pass

        self.pluginIsInitializing = False

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedPrefsConfigUi(self, values_dict=None, user_cancelled=False):  # noqa
        """
        Standard Indigo method called when plugin preferences dialog is closed.

        :param indigo.Dict values_dict:
        :param bool user_cancelled:
        :return:
        """
        if not user_cancelled:
            # Ensure that self.pluginPrefs includes any recent changes.
            for k in values_dict:
                self.pluginPrefs[k] = values_dict[k]

            # Debug Logging
            self.debug_level = int(values_dict.get('showDebugLevel', "30"))
            self.indigo_log_handler.setLevel(self.debug_level)
            indigo.server.log(
                f"Debugging on (Level: {DEBUG_LABELS[self.debug_level]} ({self.debug_level})"
            )

            self.logger.debug("Plugin prefs saved.")

        else:
            self.logger.debug("Plugin prefs cancelled.")

        return values_dict

    # =============================================================================
    def deviceUpdated(self, orig_dev=None, new_dev=None):  # noqa
        """
        Title Placeholder

        Body placeholder

        :param indigo.Dict orig_dev:
        :param indigo.Dict new_dev:
        :return:
        """
        # Call the base implementation first just to make sure all the right things happen
        # elsewhere.
        indigo.PluginBase.deviceUpdated(self, orig_dev, new_dev)

        # If "Subscribe to Changes" is enabled
        if self.pluginPrefs.get('enableSubscribeToChanges', False):

            track_list = self.pluginPrefs.get('subscribedDevices', '')
            if track_list == '':
                subscribed_items = []
            else:
                subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]

            # If dev id in list of tracked items
            if orig_dev.id in subscribed_items:

                # Attribute changes
                exclude_list = (
                    'globalProps',
                    'lastChanged',
                    'lastSuccessfulComm',
                    'ownerProps',
                    'states'
                )
                attrib_list = [
                    attr for attr in dir(orig_dev) if not callable(getattr(orig_dev, attr))
                    and '__' not in attr and attr not in exclude_list
                ]
                attrib_dict = {
                    attrib: (getattr(orig_dev, attrib), getattr(new_dev, attrib))
                    for attrib in attrib_list
                    if getattr(orig_dev, attrib) != getattr(new_dev, attrib)
                }

                # Property changes
                orig_props = dict(orig_dev.ownerProps)
                new_props = dict(new_dev.ownerProps)
                props_dict = {
                    key: (orig_props[key], new_props[key]) for key in orig_props
                    if orig_props[key] != new_props[key]
                }

                # State changes
                state_dict = {
                    key: (orig_dev.states[key], val)
                    for key, val in new_dev.states.items()
                    if key not in orig_dev.states or val != orig_dev.states[key]
                }

                if len(attrib_dict) > 0 or len(state_dict) > 0 or len(props_dict) > 0:
                    indigo.server.log(
                        f"\nDevice Changes: [{new_dev.name}]\n"
                        f"{'Attr:':<8}{attrib_dict}\n"
                        f"{'Props:':<8}{props_dict}\n"
                        f"{'States:':<8}{state_dict}"
                    )

    # =============================================================================
    def getMenuActionConfigUiValues(self, menu_id=""):  # noqa
        """
        Title Placeholder

        Body placeholder

        :param str menu_id:
        :return indigo.Dict:
        """
        # Grab the setting values for the "Subscribe to Changes" tool
        if menu_id == 'subscribeToChanges':

            changes_dict = indigo.Dict()
            changes_dict['enableSubscribeToChanges'] = (
                self.pluginPrefs.get('enableSubscribeToChanges', False)
            )
            changes_dict['subscribedDevices'] = self.pluginPrefs.get('subscribedDevices', '')

            return_value = changes_dict

        else:
            return_value = indigo.Dict()

        return return_value

    # =============================================================================
    def sendDevicePing(self, dev_id=0, suppress_logging=False):  # noqa
        """
        Standard Indigo method called when a ping request sent to a plugin device.

        :param int dev_id: Indigo device ID.
        :param bool suppress_logging: Suppress logging? [True | False]
        :return dict:
        """
        indigo.server.log("Multitool Plugin devices do not support the ping function.")
        return {'result': 'Failure'}

    # =============================================================================
    def startup(self):
        """
        Title Placeholder

        :return:
        """
        # =========================== Audit Indigo Version ============================
        self.Fogbert.audit_server_version(min_ver=2022)

        # ================ Subscribe to Indigo Object Changes =================
        if self.pluginPrefs.get('enableSubscribeToChanges', False):
            self.logger.warning(
                "You have subscribed to device and variable changes. Disable this feature if not "
                "in use."
            )
            indigo.devices.subscribeToChanges()
            indigo.variables.subscribeToChanges()
            # indigo.triggers.subscribeToChanges()      # Not implemented
            # indigo.schedules.subscribeToChanges()     # Not implemented
            # indigo.actionGroups.subscribeToChanges()  # Not implemented
            # indigo.controlPages.subscribeToChanges()  # Not implemented

    # =============================================================================
    def variableUpdated(self, orig_var, new_var):  # noqa
        """
        Title Placeholder

        :param indigo.Dict orig_var:
        :param indigo.Dict new_var:
        :return:
        """
        # Call the base implementation first just to make sure all the right things happen elsewhere
        indigo.PluginBase.variableUpdated(self, orig_var, new_var)

        # If "Subscribe to Changes" is enabled
        if self.pluginPrefs.get('enableSubscribeToChanges', False):

            track_list = self.pluginPrefs.get('subscribedDevices', '')
            if track_list == '':
                subscribed_items = []
            else:
                subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]

            # If var id in list of tracked items
            if orig_var.id in subscribed_items:

                # Attribute changes
                exclude_list = ('globalProps', 'lastChanged', 'lastSuccessfulComm')
                attrib_list = [
                    attr for attr in dir(orig_var) if not callable(getattr(orig_var, attr))
                    and '__' not in attr and attr not in exclude_list
                ]
                attrib_dict = {
                    attrib: (getattr(orig_var, attrib), getattr(new_var, attrib))
                    for attrib in attrib_list
                    if getattr(orig_var, attrib) != getattr(new_var, attrib)
                }

                # Variable value
                val_dict = {}
                if orig_var.value != new_var.value:
                    val_dict = {new_var.name: (orig_var.value, new_var.value)}

                if len(attrib_dict) > 0 or len(val_dict):
                    indigo.server.log(
                        f"\nVariable Changes: [{new_var.name}]\n"
                        f"{'Attr:':<8}{attrib_dict}\n"
                        f"{'Value':<8}{val_dict}"
                    )

    # =============================================================================
    def validateActionConfigUi(self, action_dict, type_id, device_id):  # noqa
        """
        Title Placeholder

        Body placeholder

        :param indigo.Dict action_dict:
        :param int type_id:
        :param int device_id:
        :return:
        """
        error_msg_dict = indigo.Dict()

        # ========================== Modify Numeric Variable ==========================
        if type_id == "modify_numeric_variable":
            var = indigo.variables[int(action_dict['list_of_variables'])]
            expr = action_dict['modifier']

            try:
                float(var.value)
            except ValueError:
                error_msg_dict['list_of_variables'] = "The variable value must be a real number."

            try:
                self.Eval.eval_expr(var.value + expr)
            except (SyntaxError, TypeError):
                error_msg_dict['modifier'] = (
                    "Please enter a valid formula. Click the help icon below (?) for details."
                )

        # =========================== Modify Time Variable ============================
        if type_id == "modify_time_variable":
            var = indigo.variables[int(action_dict['list_of_variables'])]

            try:
                dt.datetime.strptime(var.value, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                error_msg_dict['list_of_variables'] = (
                    "The variable value must be a POSIX timestamp."
                )

            for val in ('days', 'hours', 'minutes', 'seconds'):
                try:
                    float(action_dict[val])
                except ValueError:
                    error_msg_dict[val] = "The value must be a real number."

        if len(error_msg_dict) > 0:
            error_msg_dict['showAlertText'] = (
                "Configuration Errors\n\nThere are one or more settings that need to be corrected. "
                "Fields requiring attention will be highlighted."
            )
            return False, action_dict, error_msg_dict

        return True, action_dict

    # =============================================================================
    # ============================== Plugin Methods ===============================
    # =============================================================================
    def __dummyCallback__(self, values_dict=None, type_id=""):
        """
        Dummy callback to cause refresh of dialog elements

        The __dummyCallback__ method is used and a placeholder callback to force a refresh of
        dialog elements based for controls with dynamic refresh attributes.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """

    # =============================================================================
    def about_indigo(self):
        """
        Prints information about the Indigo environment to the events log

        The about_indigo method prints select Indigo environment information to the Indigo events
        log. It can be a useful tool to get a user to quickly print relevant environment
        information for troubleshooting.

        :return:
        """
        self.logger.debug("Call to about_indigo")

        lat_long  = indigo.server.getLatitudeAndLongitude()
        latitude  = lat_long[0]
        longitude = lat_long[1]
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

    # =============================================================================
    def color_picker(self, values_dict=None, type_id=""):  # noqa
        """
        Print color information to the Indigo events log

        Write color information to the Indigo events log to include the raw, hex, and RGB values.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """
        self.logger.debug("Call to color_picker")

        if not values_dict['chosenColor']:
            values_dict['chosenColor'] = "FF FF FF"
        indigo.server.log(f"Raw: {values_dict['chosenColor']}")
        indigo.server.log(f"Hex: #{values_dict['chosenColor'].replace(' ', '')}")
        indigo.server.log(
            f"RGB: {tuple([int(thing, 16) for thing in values_dict['chosenColor'].split(' ')])}"
        )
        return True

    # =============================================================================
    def device_dependencies(self, values_dict=None, type_id=""):  # noqa
        """
        Print a list of device dependencies to the Indigo events log

        The device_dependencies method prints a list of known dependencies for a selected Indigo
        device.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """
        self.logger.debug("Call to device_dependencies")
        err_msg_dict = indigo.Dict()

        try:
            dependencies = indigo.device.getDependencies(int(values_dict['listOfDevices']))
            name = indigo.devices[int(values_dict['listOfDevices'])].name
            indigo.server.log(f"{' ' + name + ' Dependencies':{'='}^80}")
            indigo.server.log(f"{dependencies}")
            return_value = (True, values_dict)

        except Exception as err:
            self.logger.critical("Error: ", exc_info=True)
            self.logger.critical("Error obtaining dependencies.")
            err_msg_dict['listOfDevices'] = "Problem communicating with the device."
            err_msg_dict['showAlertText'] = f"Device dependencies Error.\n\nReason: {err}"
            return_value = (False, values_dict, err_msg_dict)

        return return_value

    # =============================================================================
    def device_inventory(self, values_dict=None, type_id=""):  # noqa
        """
        Print an inventory of Indigo devices to the Indigo events log

        The device_inventory method prints an inventory of all Indigo devices to the Indigo events
        log.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """
        self.logger.debug("Call to device_inventory")

        filter_item = ""
        inventory = []

        if values_dict['typeOfThing'] not in ('Other', 'pickone'):
            filter_item = values_dict['typeOfThing']
            inventory = [
                [dev.id, dev.address, dev.name, dev.lastChanged, dev.enabled] for dev
                in indigo.devices.iter(filter=filter_item)
            ]

        elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
            filter_item = values_dict['customThing']
            inventory = [
                [dev.id, dev.address, dev.name, dev.lastChanged, dev.enabled] for dev
                in indigo.devices.iter(filter=filter_item)
            ]

        if len(inventory) > 0:
            # ====================== Generate Custom Table Settings =======================
            x0 = max([len(f"{thing[0]}") for thing in inventory]) + 2
            x1 = max([len(f"{thing[1]}") for thing in inventory]) + 2
            x2 = max([len(f"{thing[2]}") for thing in inventory]) + 2
            x3 = max([len(f"{thing[3]}") for thing in inventory])
            x4 = max([len(f"{thing[4]}") for thing in inventory])
            table_width = sum((x0, x1, x2, x3, x4)) + 6

            # ============================= Output the Header =============================
            indigo.server.log(f"{f' Inventory of {filter_item} Devices ':=^{table_width}}")
            indigo.server.log(
                f"{'ID':<{x0}} {'Addr':<{x1}} "
                f"{'Name':<{x2}} "
                f"{'Last Changed':<{x3}} "
                f"{'Enabled':<3}"
            )
            indigo.server.log("=" * table_width)

            # ============================= Output the Table ==============================
            for thing in inventory:
                indigo.server.log(
                    f"{thing[0]:<{x0}} "
                    f"{f'[{thing[1]}]':<{x1}} "
                    f"{thing[2]:<{x2}} "
                    f"{dt.datetime.strftime(thing[3], '%Y-%m-%d %H:%M:%S'):<{x3}} "
                    f"[ {thing[4]:^3} ]"
                )
        else:
            if values_dict['typeOfThing'] not in ('Other', 'pickone'):
                indigo.server.log(f"No {values_dict['typeOfThing']} devices found.")
            elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
                indigo.server.log(f"No {values_dict['customThing']} devices found.")

        return values_dict

    # =============================================================================
    def device_last_successful_comm(self):
        """
        Print information on the last successful communication with a device

        The device_last_successful_comm method prints information on the last successful
        communication with each Indigo device to the Indigo events log.

        :return:
        """
        self.logger.debug("Call to device_last_successful_comm")

        # Get the data we need
        table = [(dev.id, dev.name, dev.lastSuccessfulComm) for dev in indigo.devices.iter()]

        # Sort the data from newest to oldest
        # table = sorted(table, key=lambda (dev_id, name, comm): comm, reverse=True)
        table = sorted(table, key=lambda t: t[::-1], reverse=True)

        # Find the length of the longest device name
        length = 0
        for element in table:
            if len(element[1]) > length:
                length = len(element[1])

        # Output the result
        indigo.server.log(f"{' Device Last Successful Comm ':=^100}")
        indigo.server.log(f"{'ID':<14}{'Name':<{length + 1}} Last Comm Success")
        indigo.server.log('=' * 100)
        for element in table:
            indigo.server.log(f"{element[0]:<14}{element[1]:<{length}}  {element[2]}")

    # =============================================================================
    def device_to_beep(self, values_dict=None, type_id=""):  # noqa
        """
        Send a beep request to a device

        The device_to_beep method will send a beep request to a selected Indigo device. Only select
        devices support the beep request and only enabled devices are displayed for selection.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """
        self.logger.debug("Call to device_to_beep")

        err_msg_dict = indigo.Dict()

        try:
            name = indigo.devices[int(values_dict['listOfDevices'])].name
            indigo.server.log(f"{' Send Beep to ' + name + ' ':{'='}^80}")
            indigo.device.beep(int(values_dict['listOfDevices']), suppressLogging=False)
            return True

        except ValueError:
            err_msg_dict['listOfDevices'] = "You must select a device to receive the beep request"
            err_msg_dict['showAlertText'] = "Beep Error.\n\nReason: No device selected."
            return False, values_dict, err_msg_dict

        except Exception as err:
            self.logger.critical("Error: ", exc_info=True)
            self.logger.critical("Error sending beep request.")
            err_msg_dict['listOfDevices'] = "Problem communicating with the device."
            err_msg_dict['showAlertText'] = f"Beep Error.\n\nReason: {err}"
            return False, values_dict, err_msg_dict

    # =============================================================================
    def device_to_ping(self, values_dict=None, type_id=""):  # noqa
        """
        Send a ping request to a device

        The device_to_ping method will send a ping request to a selected Indigo device. Only
        enabled devices are displayed. Plugin devices must support sendDevicePing method and plugin
        must be enabled.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """
        self.logger.debug("Call to device_to_ping")

        dev_id = int(values_dict['listOfDevices'])
        dev = indigo.devices[dev_id]

        try:
            if dev.enabled:
                indigo.server.log(f"{'Pinging device: ' + dev.name:{'='}^80}")
                result = indigo.device.ping(dev_id, suppressLogging=False)
                if result['Success']:
                    indigo.server.log(
                        f"Ping \"{dev.name}\" success. Time: {result['TimeDelta']/1000.0} seconds."
                    )
                else:
                    indigo.server.log("Ping fail.")
        except (ValueError, TypeError):
            self.logger.critical("Error: ", exc_info=True)
            self.logger.critical("Error sending ping.")

    # =============================================================================
    def dict_to_print(self, fltr="", values_dict=None, target_id=""):  # noqa
        """
        Return a list of Indigo objects for inspection

        The dict_to_print method will return a list of objects for inspection. Objects that are
        supported include Actions, Control Pages, Devices, Schedules, Triggers, and variables. It
        is called by the Object Dictionary... menu item in conjunction with the results_output
        method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param int target_id:
        :return:
        """
        self.logger.debug("Call to dict_to_print")

        if not values_dict:
            return_value = [("none", "None")]
        else:
            return_value = [
                (thing.id, thing.name) for thing in getattr(indigo, values_dict['classOfThing'])
            ]

        return return_value

    # =============================================================================
    def environment_path(self):
        """
        Print the Indigo server's environment path variable to the Indigo Events log

        the environment_path method outputs the value of the server computer's environment path
        variable to the Indigo events log. This can help with trouble-shooting--for example, when
        an expected import statement fails.

        :return:
        """
        self.logger.debug("Call to environment_path")

        indigo.server.log(f"{' Current System Path ':{'='}^130}")
        for p in sys.path:
            indigo.server.log(p)
        indigo.server.log(f"{' (Sorted) ':{'='}^130}")
        for p in sorted(sys.path):
            indigo.server.log(p)

    # =============================================================================
    def error_inventory(self, values_dict=None, type_id=""):  # noqa
        """
        Create an inventory of error messages appearing in the Indigo Logs.

        The error_inventory method will scan log files and parse out any log lines than contain the
        term 'error'. It is agnostic about whether the log line is an actual error or a debug
        statement that contains the term error.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """
        self.logger.debug("Call to error_inventory")

        check_list = (' Err ', ' err ', 'Error', 'error')
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

    # =============================================================================
    def generator_device_list(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        """
        Returns a list of plugin devices.

        The generator_device_list method passes a list of Indigo devices to the calling control.
        It is a connector to the generator which is located in the DLFramework module.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :return:
        """
        self.logger.debug("generator_device_list() called.")

        return self.Fogbert.deviceList(dev_filter=fltr)

    # =============================================================================
    def generator_variable_list(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        """
        Returns a list of plugin variables.

        The generator_device_list method passes a list of Indigo devices to the calling control. It
        is a connector to the generator which is located in the DLFramework module.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :return:
        """
        self.logger.debug("generator_variable_list() called.")

        return self.Fogbert.variableList()

    # =============================================================================
    def generator_enabled_device_list(
            self, fltr="", values_dict=None, type_id="", target_id=0  # noqa
    ):
        """
        Returns a list of enabled plugin devices.

        The generator_enabled_device_list passes a list of enabled Indigo devices to the calling
        control. It is a connector to the generator which is located in theDLFramework module.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :return:
        """
        self.logger.debug("generator_device_list() called.")
        return self.Fogbert.deviceListEnabled(dev_filter=fltr)

    # =============================================================================
    def generator_dev_var(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        """
        Return a list of Indigo devices and variables

        The generator_dev_var method collects IDs and names for all Indigo devices and variables.
        It creates a list of the form:

        [(dev.id, dev.name), (var.id, var.name)].

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :return:
        """
        self.logger.debug("generator_dev_var() called.")
        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_state_or_value(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        """
        Return a list of device states and variable values

        The generator_state_or_value() method returns a list to populate the relevant device states
        or variable value to populate a menu control.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :return:
        """
        return self.Fogbert.generatorStateOrValue(values_dict.get('devVarMenu', ""))

    # =============================================================================
    def generator_substitutions(self, values_dict=None, type_id="", target_id=0):  # noqa
        """
        Generate the construct for an Indigo substitution

        The generator_substitutions method is used with the Substitution Generator. It is the
        callback that's used to create the Indigo substitution construct.

        :param indigo.Dict values_dict:
        :return str type_id:
        :return int target_id:
        :return:
        """
        self.logger.debug("generator_substitutions() called.")

        dev_var_id    = values_dict['devVarMenu']
        dev_var_value = values_dict['generator_state_or_value']

        if int(values_dict['devVarMenu']) in indigo.devices.keys():
            indigo.server.log(f"Indigo Device Substitution: %%d:{dev_var_id}:{dev_var_value}%%")

        else:
            indigo.server.log(f"Indigo Variable Substitution: %%v:{dev_var_id}%%")

        values_dict['devVarMenu'] = ''
        values_dict['generator_state_or_value'] = ''

        return values_dict

    # =============================================================================
    def get_serial_ports(self, values_dict=None, type_id=""):  # noqa
        """
        Print a list of serial ports to the Indigo events log

        The get_serial_ports method prints a list of available serial ports to the Indigo events
        log.

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        self.logger.debug("Call to get_serial_ports")

        # ========================= Filter Bluetooth Devices ==========================
        if values_dict.get('ignoreBluetooth', False):
            port_filter = "indigo.ignoreBluetooth"
        else:
            port_filter = ""

        # ============================= Print the Report ==============================
        indigo.server.log(f"{' Current Serial Ports ':=^80}")

        for k, v in indigo.server.getSerialPorts(filter=f"{port_filter}").items():
            indigo.server.log(f"{k:40} {v}")

        return True

    # =============================================================================
    def indigo_inventory(self):  # noqa
        """
        Title Placeholder

        Body placeholder

        :return:
        """
        # ============================== Build Inventory ==============================
        inventory = {
            'Action Groups': [],
            'Control Pages': [],
            'Devices': [],
            'Schedules': [],
            'Triggers': [],
            'Variables': []
        }

        for action in indigo.actionGroups.iter():
            inventory['Action Groups'].append(
                (
                    action.id,
                    action.name,
                    action.folderId,
                    indigo.actionGroups.folders.getName(action.folderId)
                )
            )

        for page in indigo.controlPages.iter():
            inventory['Control Pages'].append(
                (
                    page.id,
                    page.name,
                    page.folderId,
                    indigo.controlPages.folders.getName(page.folderId)
                )
            )

        for dev in indigo.devices.iter():
            inventory['Devices'].append(
                (
                    dev.id,
                    dev.name,
                    dev.folderId,
                    indigo.devices.folders.getName(dev.folderId)
                )
            )

        for schedule in indigo.schedules.iter():
            inventory['Schedules'].append(
                (
                    schedule.id,
                    schedule.name,
                    schedule.folderId,
                    indigo.schedules.folders.getName(schedule.folderId)
                )
            )

        for trigger in indigo.triggers.iter():
            inventory['Triggers'].append(
                (
                    trigger.id,
                    trigger.name,
                    trigger.folderId,
                    indigo.triggers.folders.getName(trigger.folderId)
                )
            )

        for var in indigo.variables.iter():
            inventory['Variables'].append(
                (
                    var.id,
                    var.name,
                    var.folderId,
                    indigo.variables.folders.getName(var.folderId)
                )
            )

        # ====================== Generate Custom Table Settings =======================
        col_0 = []
        col_1 = []
        col_2 = []
        col_3 = []

        for key in inventory:
            col_0 += [item[0] for item in inventory[key]]
            col_1 += [item[1] for item in inventory[key]]
            col_2 += [item[2] for item in inventory[key]]
            col_3 += [item[3] for item in inventory[key]]

        col0 = max([len(f"{item}") for item in col_0]) + 2
        col1 = max([len(f"{item}") for item in col_1]) + 2
        col2 = max([len(f"{item}") for item in col_2]) + 2
        col3 = max([len(f"{item}") for item in col_3]) + 2

        table_width = sum([col0, col1, col2, col3])

        # ============================= Output the Table ==============================
        for object_type in sorted(inventory):
            header = f" {object_type} "
            indigo.server.log(f"{header:{'='}^{table_width}}")

            indigo.server.log(
                f"{'ID':{col0}}{'Name':{col1}}{'Folder ID':{col2}}{'Folder Name':{col3}}"
            )
            indigo.server.log("=" * table_width)

            for element in inventory[object_type]:
                indigo.server.log(
                    f"{element[0]:<{col0}}"
                    f"{element[1]:<{col1}}"
                    f"{element[2]:<{col2}}"
                    f"{element[3]:<{col3}}"
                )

        indigo.server.log(f"{' Summary ':{'='}^{table_width}}")

        for object_type in sorted(inventory):
            indigo.server.log(f"{object_type:15}{len(inventory[object_type])}")

    # =============================================================================
    def inspect_method(self, values_dict=None, type_id=""):  # noqa
        """
        Print the signature of an Indigo method to the Indigo events log

        The inspect_method method will inspect a selected Indigo method and print the target
        method's signature to the Indigo events log. This is useful when the signature of an Indigo
        method is unknown.  It will return a list of attributes passed by the Indigo method.  For
        example,

           Multitool    self.closedPrefsConfigUi: ArgSpec(args=['self', 'valuesDict',
                        'userCancelled'], varargs=None, keywords=None, defaults=None)
           Multitool    Docstring:  User closes config menu.
                        The validatePrefsConfigUI() method will also be called.

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        self.logger.debug("Call to inspect_method")

        method = getattr(self, values_dict['list_of_plugin_methods'])
        signature = inspect.getfullargspec(method)
        indigo.server.log(f"self.{values_dict['list_of_plugin_methods']}: {signature}")
        doc_string = getattr(self, values_dict['list_of_plugin_methods']).__doc__
        indigo.server.log(f"Docstring: {doc_string}", isError=False)

    # =============================================================================
    def installed_plugins(self):

        """
        Print a list of installed plugins to the Indigo events log

        The installed_plugins method will print a list of installed plugins to the Indigo events
        log along with the plugin's bundle identifier. In instances where the plugin is disabled,
        [Disabled] will be appended to the log line.

        :return:
        """
        self.logger.debug("Call to installed_plugins")

        plugin_name_list    = []
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

    # =============================================================================
    def list_of_plugin_methods(self, fltr="", values_dict=None, target_id=""):  # noqa
        """
        Generates a list of Indigo plugin methods for inspection

        The list_of_plugin_methods method will generate a list of Indigo plugin methods available
        for inspection. It is used to populate the list of methods control for the
        Methods - Plugin Base... tool.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str target_id:
        :return:
        """
        list_of_attributes = []

        for method in dir(indigo.PluginBase):
            try:
                inspect.getfullargspec(getattr(indigo.PluginBase, method))
                if values_dict.get('include_hidden_methods', False):
                    list_of_attributes.append((method, f"self.{method}"))
                else:
                    if not method.startswith('_'):
                        list_of_attributes.append((method, f"self.{method}"))

            except (AttributeError, TypeError):
                continue

        return list_of_attributes

    # =============================================================================
    def list_of_indigo_classes(self, fltr="", values_dict=None, target_id=""):  # noqa
        """
        Generates a list of Indigo classes for inspection

        The list_of_indigo_classes method will generate a list of Indigo classes available for
        inspection. It is used to populate the list of classes control for the
        Methods - Indigo Base... tool.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str target_id:
        :return:
        """
        # If user elects to display hidden methods.
        if values_dict.get('include_hidden_methods', False):
            result = [(f"{_}", f"indigo.{_}") for _ in sorted(dir(indigo), key=str.lower)]
        else:
            result = [
                (f"{_}", f"indigo.{_}") for _ in sorted(dir(indigo), key=str.lower)
                if not _.startswith('_')
            ]

        return result

    # =============================================================================
    def list_of_indigo_methods(self, fltr="", values_dict=None, target_id=""):  # noqa
        """
        Generates a list of Indigo methods for inspection

        The list_of_indigo_methods method will generate a list of Indigo methods available for
        inspection. It is used to populate the list of methods control for the
        Methods - Indigo Base... tool.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str target_id:
        :return:
        """
        return_value = []
        try:
            if len(values_dict.keys()) == 0:
                pass

            else:
                indigo_classes = getattr(indigo, values_dict['list_of_indigo_classes'])
                directory = dir(indigo_classes)

                if values_dict.get('include_hidden_methods', False):
                    return_value = [_ for _ in directory]
                else:
                    return_value = [_ for _ in directory if not _.startswith('_')]

        except AttributeError:
            pass

        return return_value

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict=None, type_id=""):  # noqa
        """
        Logs the inspection of the passed class/method

        The log_of_method method will generate an inspection of the passed class and method (i.e.,
        indigo.server.log) and write the result to the Indigo Activity Log.

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        method_to_call = getattr(indigo, values_dict['list_of_indigo_classes'])
        method_to_call = getattr(method_to_call, values_dict['list_of_indigo_methods'])
        inspector = inspect.getdoc(method_to_call)
        indigo.server.log(f"\nindigo.{values_dict['list_of_indigo_classes']}.{inspector}")

    # =============================================================================
    def man_page(self, values_dict=None, type_id=""):  # noqa
        """
        Title Placeholder

        Body placeholder

        :param class values_dict:
        :param str type_id:
        :return:
        """
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
            self.logger.exception(f"{err} [{return_code}]")

        return True

    # =============================================================================
    def modify_numeric_variable(self, action_group):
        """
        Title Placeholder

        Body placeholder

        :param indigo.ActionGroup action_group:
        :return:
        """
        var_id = int(action_group.props['list_of_variables'])
        var    = indigo.variables[var_id]
        expr   = action_group.props['modifier']

        try:
            answer = self.Eval.eval_expr(var.value + expr)
            indigo.variable.updateValue(var_id, f"{answer}")
            return_value = True

        except SyntaxError:
            self.logger.critical("Error: ", exc_info=True)
            self.logger.critical(f"Error modifying variable {var.name}.")
            return_value = False

        return return_value

    # =============================================================================
    def modify_time_variable(self, action_group):
        """
        Title Placeholder

        Body placeholder

        :param indigo.ActionGroup action_group:
        :return:
        """
        var_id  = int(action_group.props['list_of_variables'])
        var     = indigo.variables[var_id]
        expr    = action_group.props['modifier']
        seconds = action_group.props['seconds']
        minutes = action_group.props['minutes']
        hours   = action_group.props['hours']
        days    = action_group.props['days']
        ops     = {"add": operator.add, "subtract": operator.sub}

        try:
            d   = dt.datetime.strptime(var.value, "%Y-%m-%d %H:%M:%S.%f")
            td  = dt.timedelta(
                days=float(days),
                hours=float(hours),
                minutes=float(minutes),
                seconds=float(seconds)
            )
            d_s = ops[expr](d, td)
            indigo.variable.updateValue(var_id, f"{d_s}")
            return True

        except ValueError:
            self.logger.critical("Error: ", exc_info=True)
            self.logger.critical(f"Error modifying variable {var.name}.")
            return False

    # =============================================================================
    def remove_all_delayed_actions(self, values_dict=None, type_id=""):  # noqa
        """
        Removes all delayed actions from the Indigo server

        The remove_all_delayed_actions method is a convenience tool to remove all delayed actions
        from the Indigo server.

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        self.logger.debug("Call to remove_all_delayed_actions")
        indigo.server.removeAllDelayedActions()
        return True

    # =============================================================================
    def running_plugins(self):
        """
        Print a list of running plugins to the Indigo events log

        The running_plugins method prints a table of Indigo plugins that are currently enabled. It
        includes system and other information that is useful for troubleshooting purposes.

        Display the uid, pid, parent pid, recent CPU usage, process start time, controlling tty,
        elapsed CPU usage, and the associated command.  If the -u option is also used, display the
        username rather than the numeric uid.  When -o or -O is used to add to the display
        following -f, the command field is not truncated as severely as it is in other formats.

        :return:
        """
        self.logger.debug("Call to running_plugins")

        with subprocess.Popen(
                "/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE) as proc:

            ret = proc.communicate()[0]

        indigo.server.log(f"\n{' Running Plugins (/bin/ps -ef) ':{'='}^120}")
        indigo.server.log(
            f"\n  uid - pid - parent pid - recent CPU usage - process start time - controlling tty "
            f"- elapsed CPU usage - associated command\n\n{ret.decode('utf-8')}"
        )

    # =============================================================================
    def results_output(self, values_dict=None, caller=None):
        """
        Print an Indigo object's properties dict to the Indigo events log

        The results_output method formats an object properties dictionary for output to the Indigo
        events log. It's used in conjunction with the Object Dictionary... tool.

        :param indigo.Dict values_dict:
        :param str caller:
        :return:
        """
        self.logger.debug("Call to results_output")
        self.logger.debug(f"Caller: {caller}")

        thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]
        indigo.server.log(f"{thing.name:{'='}^80}")
        indigo.server.log(f"\n{thing}")
        indigo.server.log("=" * 80)

    # =============================================================================
    def send_status_request(self, values_dict=None, type_id=""):  # noqa
        """
        Send a status request to an Indigo object

        The send_status_request method will send a status request inquiry to a selected Indigo
        object. Note that not all objects support a status request and plugin devices that support
        status requests must have their host plugin enabled. Further, only enabled objects are
        available for a status request.

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        self.logger.debug("Call to send_status_request")
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(f"{' Sending Status Request ':{'='}^80}")
            indigo.device.statusRequest(int(values_dict['listOfDevices']), suppressLogging=False)
            return True

        except Exception as err:
            self.logger.critical("Error sending status Request.")
            err_msg_dict['listOfDevices'] = "Problem communicating with the device."
            err_msg_dict['showAlertText'] = f"Status Request Error.\n\nReason: {err}"
            return False, values_dict, err_msg_dict

    # =============================================================================
    def speak_string(self, values_dict=None, type_id=""):  # noqa
        """
        Speak a string

        The speak_string method takes a user-input string and sends it for speech on the Indigo
        server. The method supports Indigo substitutions and is useful when testing substitution
        strings.

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        self.logger.debug("Call to speak_string")
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(f"{' Speaking ':{'='}^80}")
            indigo.server.log(self.substitute(values_dict['thingToSpeak']))
            indigo.server.speak(self.substitute(values_dict['thingToSpeak']))

            return_value = (True, values_dict)

        except Exception as err:
            self.logger.critical("Error sending status Request.")
            err_msg_dict['listOfDevices'] = "Problem communicating with the device."
            err_msg_dict['showAlertText'] = f"Status Request Error.\n\nReason: {err}"
            return_value = (False, values_dict, err_msg_dict)

        return return_value

    # =============================================================================
    def subscribed_to_changes(self, values_dict=None, type_id=""):  # noqa
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
        # If user changes subscription preference, set flag for plugin restart (see __init__)
        if self.pluginPrefs['enableSubscribeToChanges'] == values_dict['enableSubscribeToChanges']:
            restart_required = False
        else:
            restart_required = True

        # Save preferences to plugin config for storage
        self.pluginPrefs['enableSubscribeToChanges'] = values_dict['enableSubscribeToChanges']
        self.pluginPrefs['subscribedDevices']        = values_dict['subscribedDevices']

        if restart_required:
            indigo.server.log("Preparing to restart plugin...")
            self.sleep(2)

            # plugin = indigo.server.getPlugin("com.fogbert.indigoplugin.multitool")
            # plugin.restart(waitUntilDone=False)

            self.restartPlugin(message="", isError=False)

        return True

    # =============================================================================
    def substitution_generator(self, values_dict=None, type_id=""):  # noqa
        """
        Generate an Indigo substitution string

        The substitution_generator method is used to construct Indigo substitution string segments
        from Indigo objects.  For example,

            Indigo Device Substitution: %%d:978421449:stateName%%

        :param indigo.Dict values_dict:
        :param str type_id:
        :return:
        """
        self.logger.debug("Call to substitution_generator")

        err_msg_dict = indigo.Dict()
        substitution_text = values_dict.get('thingToSubstitute', '')
        result = self.substitute(substitution_text)

        if substitution_text == '':
            return_value = (True, values_dict)

        elif result:
            indigo.server.log(result)
            return_value = (True, values_dict)

        else:
            err_msg_dict['thingToSubstitute'] = "Invalid substitution string."
            err_msg_dict['showAlertText'] = (
                "Substitution Error.\n\nYour substitution string is invalid. See the Indigo log "
                "for available information."
            )
            return_value = (False, values_dict, err_msg_dict)

        return return_value


class Bar:

    @staticmethod
    def add(a, b):
        return a + b
