# noqa pylint: disable=too-many-lines, line-too-long, invalid-name, unused-argument, redefined-builtin, broad-except, fixme

"""
Multitool Indigo Plugin
author: DaveL17

THe Multitool plugin provides a set of tools for use in using Indigo and for use when developing
plugins for Indigo.
"""

# ================================== IMPORTS ==================================
# Built-in modules
import datetime as dt
import json
import logging
from queue import Queue
import platform
import re
import subprocess
from threading import Thread
from typing import Any, Callable
import lorem  # noqa https://github.com/sfischer13/python-lorem
# import unittest

import indigo  # noqa

# My modules
import DLFramework.DLFramework as Dave  # noqa
from constants import DEBUG_LABELS, FILTER_LIST
from plugin_defaults import kDefaultPluginPrefs  # noqa
from Tools import *

# =================================== HEADER ==================================
__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'Multitool Plugin for the Indigo Smart Home Software Platform'
__version__   = '2025.2.3'


# =============================================================================
class Plugin(indigo.PluginBase):
    """Standard Indigo Plugin Class providing the Multitool feature set."""
    def __init__(self, plugin_id: str, plugin_display_name: str, plugin_version: str, plugin_prefs: indigo.Dict) -> None:
        """Plugin initialization.

        Args:
            plugin_id: Unique plugin identifier string.
            plugin_display_name: Display name shown in the Indigo UI.
            plugin_version: Current plugin version string.
            plugin_prefs: Persistent plugin preferences dictionary.
        """
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)

        # ============================ Instance Attributes =============================
        self.pluginIsInitializing: bool = True
        self.pluginIsShuttingDown: bool = False
        self.my_triggers = {}  # Master dict of triggers

        # =============================== Debug Logging ================================
        self.debug_level: int = int(self.pluginPrefs.get('showDebugLevel', '30'))
        self.plugin_file_handler.setFormatter(logging.Formatter(Dave.LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S'))
        self.indigo_log_handler.setLevel(self.debug_level)

        # ====================== Initialize DLFramework =======================
        self.Fogbert = Dave.Fogbert(self)
        self.Eval    = Dave.evalExpr(self)

        self.cmd_queue = Queue()
        self.nq_queue = Queue()

        # Start the thread to execute commands
        self.command_thread = MyThread(target=self.execute_command, args=(self.cmd_queue, self.nq_queue))
        # self.command_thread = Thread(target=self.execute_command, args=(self.cmd_queue, self.nq_queue))
        self.command_thread.start()

    def log_plugin_environment(self) -> bool:
        """Log pluginEnvironment information when the plugin is first started.

        Returns:
            bool: True on success.
        """
        self.Fogbert.pluginEnvironment()
        return True

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedPrefsConfigUi(self, values_dict: indigo.Dict = None, user_cancelled: bool = False) -> indigo.Dict:  # noqa
        """Standard Indigo method called when the plugin preferences dialog is closed.

        Args:
            values_dict: Dictionary of preference values from the dialog.
            user_cancelled: True if the user canceled the dialog without saving.

        Returns:
            indigo.Dict: The values dictionary, updated as needed.
        """
        if not user_cancelled:
            # Ensure that self.pluginPrefs includes any recent changes.
            for k in values_dict:
                self.pluginPrefs[k] = values_dict[k]

            # Debug Logging
            self.debug_level = int(values_dict.get('showDebugLevel', "30"))
            self.indigo_log_handler.setLevel(self.debug_level)
            indigo.server.log(f"Debugging on (Level: {DEBUG_LABELS[self.debug_level]} ({self.debug_level})")
            self.logger.debug("Plugin prefs saved.")

        else:
            self.logger.debug("Plugin prefs cancelled.")

        return values_dict

    @staticmethod
    def get_attrib_dict(orig_obj: Any, new_obj: Any, exclude: tuple[str, ...]) -> dict[str, tuple[Any, Any]]:
        """Return a dict of attributes that differ between orig_obj and new_obj.

        Args:
            orig_obj: The original Indigo object (before the update).
            new_obj: The updated Indigo object (after the update).
            exclude: Tuple of attribute names to exclude from comparison.

        Returns:
            dict: Mapping of attribute name to a (old_value, new_value) tuple for
            each attribute that changed.
        """
        attrib_list = [
            attr
            for attr in dir(orig_obj)
            if not callable(getattr(orig_obj, attr))
            and "__" not in attr
            and attr not in exclude
        ]
        attrib_dict = {
            attrib: (getattr(orig_obj, attrib), getattr(new_obj, attrib))
            for attrib in attrib_list
            if getattr(orig_obj, attrib) != getattr(new_obj, attrib)
        }

        return attrib_dict

    # =============================================================================
    def deviceUpdated(self, orig_dev: indigo.Device = None, new_dev: indigo.Device = None) -> None:  # noqa
        """Standard Indigo method called when a device is updated.

        Logs attribute, property, and state changes for subscribed devices when
        the Subscribe to Changes feature is enabled.

        Args:
            orig_dev: The device object before the update.
            new_dev: The device object after the update.
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

            # If beeper id in list of tracked items
            if orig_dev.id in subscribed_items:

                # Attribute changes
                exclude_list = (
                    'globalProps',
                    'lastChanged',
                    'lastSuccessfulComm',
                    'ownerProps',
                    'states'
                )
                attrib_dict = self.get_attrib_dict(orig_obj=orig_dev, new_obj=new_dev, exclude=exclude_list)

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

    @staticmethod
    def get_device_list(filter: str = "", type_id: str = "", values_dict: indigo.Dict = None, target_id: int = 0) -> list[tuple[int, str]]:  # noqa
        """Return a list of (id, name) tuples for all plugin-owned devices.

        Args:
            filter: Device type filter string (unused).
            type_id: Device type identifier (unused).
            values_dict: Dialog values dictionary (unused).
            target_id: Target device identifier (unused).

        Returns:
            list: List of (device_id, device_name) tuples.
        """
        return [(dev.id, dev.name) for dev in indigo.devices.iter(filter="self")]

    # =============================================================================
    def getMenuActionConfigUiValues(self, menu_id: str = "") -> indigo.Dict:  # noqa
        """Standard Indigo method called when a config menu is opened.

        Args:
            menu_id: Identifier string for the menu being opened.

        Returns:
            indigo.Dict: Pre-populated values dictionary for the menu dialog.
        """
        # Grab the setting values for the "Subscribe to Changes" tool
        if menu_id == 'subscribeToChanges':
            changes_dict = indigo.Dict()
            changes_dict['enableSubscribeToChanges'] = self.pluginPrefs.get('enableSubscribeToChanges', False)
            changes_dict['subscribedDevices'] = self.pluginPrefs.get('subscribedDevices', '')
            return_value = changes_dict

        else:
            return_value = indigo.Dict()

        return return_value

    # =============================================================================
    @staticmethod
    def sendDevicePing(dev_id: int = 0, suppress_logging: bool = False) -> dict[str, str]:  # noqa
        """Standard Indigo method called when a ping request is sent to a plugin device.

        Multitool devices do not support ping; this method logs a message and
        returns a failure result.

        Args:
            dev_id: Indigo device ID of the device being pinged.
            suppress_logging: If True, suppresses log output.

        Returns:
            dict: Result dictionary with ``{'result': 'Failure'}``.
        """
        indigo.server.log("Multitool Plugin devices do not support the ping function.")
        return {'result': 'Failure'}

    # =============================================================================
    def startup(self) -> None:
        """Standard Indigo startup method.

        Subscribes to device and variable change notifications if the
        Subscribe to Changes feature is enabled in plugin preferences.
        """
        # ================ Subscribe to Indigo Object Changes =================
        if self.pluginPrefs.get('enableSubscribeToChanges', False):
            self.logger.warning(
                "You have subscribed to device and variable changes. Disable this feature if not in use."
            )
            indigo.devices.subscribeToChanges()
            indigo.variables.subscribeToChanges()
            # indigo.triggers.subscribeToChanges()      # Not implemented
            # indigo.schedules.subscribeToChanges()     # Not implemented
            # indigo.actionGroups.subscribeToChanges()  # Not implemented
            # indigo.controlPages.subscribeToChanges()  # Not implemented

    # =============================================================================
    def shutdown(self) -> None:
        """ Standard Indigo shutdown method."""
        self.command_thread.stop()

    def trigger_start_processing(self, trigger: indigo.Trigger) -> None:
        """Standard Indigo method called when a trigger starts processing.

        Registers the trigger in the local trigger dictionary, keyed by the
        offline device ID it monitors.

        Args:
            trigger: The Indigo trigger object to register.
        """
        if trigger.id not in self.my_triggers:
            self.my_triggers[trigger.pluginProps['offlineDevice']] = trigger

    # =============================================================================
    def variableUpdated(self, orig_var: indigo.Variable, new_var: indigo.Variable) -> None:  # noqa
        """Standard Indigo method called when a variable is updated.

        Logs attribute and value changes for subscribed variables when the
        Subscribe to Changes feature is enabled.

        Args:
            orig_var: The variable object before the update.
            new_var: The variable object after the update.
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

                # # Attribute changes
                exclude_list = ('globalProps', 'lastChanged', 'lastSuccessfulComm')
                attrib_dict = self.get_attrib_dict(orig_obj=orig_var, new_obj=new_var, exclude=exclude_list)

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
    def validateActionConfigUi(self, action_dict: indigo.Dict = None, type_id: str = "", device_id: int = 0) -> tuple[bool, indigo.Dict] | tuple[bool, indigo.Dict, indigo.Dict]:  # noqa
        """Standard method called to validate action config dialogs.

        Validates email addresses for the emailBatteryLevelReport action,
        and validates numeric/time variable values for their respective
        modification actions.

        Args:
            action_dict: Dictionary of action configuration values.
            type_id: Identifier for the action type being validated.
            device_id: Indigo device ID associated with the action.

        Returns:
            tuple: ``(True, action_dict)`` on success, or
            ``(False, action_dict, error_msg_dict)`` when validation fails.
        """
        error_msg_dict = indigo.Dict()

        # ========================== Modify Numeric Variable ==========================
        if type_id == "emailBatteryLevelReport":
            # addr_list = action_dict['email_address'].split(",")
            addr_list = [self.substitute(a) for a in action_dict['email_address'].replace(' ', '').split(",")]
            for addr in addr_list:
                pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                if not re.match(pattern, addr) is not None:
                    error_msg_dict['email_address'] = (
                        "One or more addresses are not valid. Check address(es) and ensure there are no extra commas."
                    )

        # ========================== Modify Numeric Variable ==========================
        if type_id == "modify_numeric_variable":
            var = indigo.variables[int(action_dict['list_of_variables'])]
            expr = self.substitute(action_dict['modifier'])

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
                error_msg_dict['list_of_variables'] = "The variable value must be a POSIX timestamp."

            for val in ('days', 'hours', 'minutes', 'seconds'):
                try:
                    float(self.substitute(action_dict[val]))
                except ValueError:
                    error_msg_dict[val] = "The value must be a real number."

        if len(error_msg_dict) > 0:
            error_msg_dict['showAlertText'] = (
                "Configuration Errors\n\nThere are one or more settings that need to be corrected. Fields requiring "
                "attention will be highlighted."
            )
            return False, action_dict, error_msg_dict

        return True, action_dict

    # =============================================================================
    # ============================== Plugin Methods ===============================
    # =============================================================================
    def __dummyCallback__(self, values_dict: indigo.Dict = None, type_id: str = "") -> None:
        """Dummy callback used to force a refresh of dialog elements.

        Assigned to controls with dynamic refresh attributes so that Indigo
        redraws the dialog when the control value changes.

        Args:
            values_dict: Dictionary of current dialog values.
            type_id: Identifier for the dialog type.
        """

    # =============================================================================
    @staticmethod
    def about_indigo(no_log: bool = False) -> bool:
        """Shim to call the About Indigo tool.

        Args:
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        about_indigo.report(no_log)
        return True

    # =============================================================================
    @staticmethod
    def battery_level_report(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> bool:  # noqa
        """Shim to call the Battery Level Report tool.

        Args:
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        battery_level.report(no_log)
        return True

    def reports_processor(self, action: indigo.Dict = None, type_id: str = "") -> indigo.Dict:  # noqa
        """Dispatch menu-invoked report actions to their corresponding methods.

        Args:
            action: Action dictionary containing the ``actionMenu`` key that
                identifies which report to run.
            type_id: Action type identifier (unused).

        Returns:
            indigo.Dict: Empty values dictionary on success, or an empty error
            dictionary if the requested action is not recognized.
        """
        values_dict = indigo.Dict()
        error_msg_dict = indigo.Dict()
        my_action = action['actionMenu']
        action_map = {
            "about_indigo": self.about_indigo,
            "battery_level_report": self.battery_level_report,
            "environment_path": self.environment_path,
            "indigo_inventory": self.indigo_inventory,
            "installed_plugins": self.installed_plugins,
            "running_plugins": self.running_plugins,
            "pip_freeze_report": self.pip_freeze_report,
            "log_plugin_environment": self.log_plugin_environment,
        }

        if my_action in action_map:
            method = getattr(self, my_action)
            method()
            return values_dict
        else:
            indigo.server.log("Trying to access an invalid report.", level=logging.WARNING)
            return error_msg_dict

    # =============================================================================
    @staticmethod
    def color_picker(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> tuple[bool, indigo.Dict]:  # noqa
        """Shim to call the ColorPicker tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            tuple: ``(True, values_dict)``
        """
        color_picker.picker(values_dict, "", no_log)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def device_inventory(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> indigo.Dict:  # noqa
        """Shim to call the Device Inventory tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            indigo.Dict: The values dictionary.
        """
        device_inventory.get_inventory(values_dict, type_id, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def device_last_successful_comm(values_dict: indigo.Dict = None, menu_item: str = "", no_log: bool = False) -> None:
        """Shim to call the Device Last Successful Comm tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            menu_item: Identifier for the menu item that triggered this call.
            no_log: If True, suppresses log output.
        """
        device_last_successful_comm.report_comms(values_dict, menu_item, no_log)

    # =============================================================================
    @staticmethod
    def device_to_beep(values_dict: indigo.Dict = None, type_id: str = "") -> tuple[bool, indigo.Dict]:  # noqa
        """Shim to call the Device Beep tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).

        Returns:
            tuple: ``(True, values_dict)``
        """
        device_beep.beeper(values_dict)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def device_to_ping(values_dict: indigo.Dict = None, type_id: str = "") -> None:  # noqa
        """Shim to call the Device Ping tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
        """
        device_ping.pinger(values_dict)

    # =============================================================================
    @staticmethod
    def dict_to_print(fltr:str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list:  # noqa
        """Shim to call the dict_to_print tool.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary passed to the tool.
            target_id: Target identifier (unused).

        Returns:
            list: The printed dict result from the tool.
        """
        return dict_to_print.print_dict(values_dict)

    # =============================================================================
    def email_battery_level_report(self, action_group: indigo.actionGroup) -> bool:
        """Email a formatted battery health report using the Email+ plugin.

        Generates the battery level report, wraps it in HTML, and sends it to
        each recipient address via the Email+ plugin. Supports Indigo variable
        substitutions in the address field.

        Args:
            action_group: Indigo action group containing ``email_address``
                (comma-separated, substitution-enabled) and ``email_device``
                (Email+ device ID) in its props.

        Returns:
            bool: True on success.
        """
        # Generate list of address(es)
        address_list = action_group.props['email_address'].replace(' ', '').split(",")
        email_device = int(action_group.props['email_device'])

        # Generate battery health report
        message = battery_level.report(no_log=True)

        # Format the report for HTML display
        style_stub = """<style>
                            html {
                                background-color: whitesmoke;
                                color: black;
                                font-family: Arial, sans-serif;
                                width: 100%;
                                overflow-x: hidden;
                                margin: 5px;
                            }
                            pre {
                                white-space: pre;
                                margin: 0;
                                font-family: 'Courier New', Courier, monospace;
                                max-width: 100%;
                                font-size: 3.5vw; /* Larger viewport-based size */
                                line-height: 1.2;
                            }
                            
                            /* Cap the size on larger screens */
                            @media screen and (min-width: 800px) {
                                pre {
                                    font-size: 14px;
                                }
                            }
                        </style>
                        """
        email_stub = f"""<!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <title>Battery Level Report</title>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        </head>
                        {style_stub}
                        <body>
                            <pre>{message}</pre>
                        </body>
                        </html>
                        """
        # Email report
        for addr in address_list:
            plugin = indigo.server.getPlugin("com.indigodomo.email")
            if plugin.isEnabled():
                plugin.executeAction(
                    "sendEmail",
                    deviceId=email_device,
                    props={
                        "emailTo": self.substitute(addr),
                        "emailSubject": "Battery Level Report",
                        "emailMessage": email_stub,
                        'emailFormat': 'html'

                    },
                )

        return True

    # =============================================================================
    @staticmethod
    def environment_path(no_log: bool = False) -> bool:
        """Shim to call the Environment Path tool.

        Args:
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        environment_path.show_path(no_log)
        return True

    # =============================================================================
    @staticmethod
    def error_inventory(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> bool:  # noqa
        """Shim to call the Error Inventory tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        error_inventory.show_inventory(values_dict, no_log)
        return True

    # =============================================================================
    def execute_command(self, command_queue: Queue, result_queue: Queue) -> None:
        """Get a command from the queue, run it, and put the output on the result queue.

        Runs in a background thread. Loops until a ``None`` sentinel is received.
        Shell output (stdout + stderr) is captured and placed on ``result_queue``.

        Args:
            command_queue: Queue from which shell command lists are consumed.
            result_queue: Queue onto which command output strings are placed.
        """
        while True:
            my_command = command_queue.get()
            my_command = ' '.join(my_command)
            if my_command is None:  # None signals the end of command execution
                break
            try:
                # Run command and log result.
                self.logger.debug("Command line argument: [ %s ]", my_command)
                indigo.server.log(
                    "Running network quality test. Results will be displayed when the test is complete (may take some "
                    "time)."
                )
                result = subprocess.check_output(my_command,
                                                 shell=True,
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)

                result_queue.put(result)
            except subprocess.CalledProcessError as e:
                result_queue.put(e.output)
            except Exception as e:
                result_queue.put(str(e))

    # =============================================================================
    def generator_device_list(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[int, str]]:  # noqa
        """Shim to call the Fogbert.deviceList utility method.

        Args:
            fltr: Device type filter string passed to deviceList.
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            target_id: Target device identifier (unused).

        Returns:
            list: List of (device_id, device_name) tuples.
        """
        return self.Fogbert.deviceList(dev_filter=fltr)

    # =============================================================================
    def generator_variable_list(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[int, str]]:  # noqa
        """Shim to call the Fogbert.variableList utility method.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            target_id: Target identifier (unused).

        Returns:
            list: List of (variable_id, variable_name) tuples.
        """
        return self.Fogbert.variableList()

    # =============================================================================
    def generator_enabled_device_list(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[int, str]]:  # noqa
        """Shim to call the Fogbert.deviceListEnabled utility method.

        Args:
            fltr: Device type filter string passed to deviceListEnabled.
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            target_id: Target device identifier (unused).

        Returns:
            list: List of (device_id, device_name) tuples for enabled devices only.
        """
        return self.Fogbert.deviceListEnabled(dev_filter=fltr)

    # =============================================================================
    # @staticmethod
    def generator_device_filter(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[str, str]]:  # noqa
        """Build a sorted, deduplicated list of device filter options.

        Combines standard Indigo device type filters with plugin identifiers
        discovered from the current device list.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            target_id: Target device identifier (unused).

        Returns:
            list: Sorted list of (filter_id, filter_label) tuples.
        """
        # Add plugin identifiers to standard filters
        _ = [FILTER_LIST.append((dev.pluginId, dev.pluginId))
             for dev in indigo.devices
             if (dev.pluginId, dev.pluginId) not in FILTER_LIST
             ]
        # Remove any duplicate tuples
        unique_tuples = list(set(FILTER_LIST))

        # Remove any empty tuples ('', '')
        filter_list = [tup for tup in unique_tuples if (len(tup[0]) + len(tup[1])) > 0]

        # Sort the list because it's a mess now.
        filter_list = sorted(filter_list)

        return filter_list

    # =============================================================================
    def generator_dev_var(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[int, str]]:  # noqa
        """Shim to call the Fogbert.deviceAndVariableList utility method.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            target_id: Target identifier (unused).

        Returns:
            list: Combined list of (id, name) tuples for devices and variables.
        """
        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_dev_var_clean(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[int, str]]:  # noqa
        """Shim to call the Fogbert.deviceAndVariableListClean utility method.

        Returns a combined device and variable list with names sanitized for
        use in UI controls.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).
            target_id: Target identifier (unused).

        Returns:
            list: Combined list of (id, name) tuples with cleaned display names.
        """
        return self.Fogbert.deviceAndVariableListClean()

    # =============================================================================
    def generator_state_or_value(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list[tuple[str, str]]:  # noqa
        """Shim to call the Fogbert.generatorStateOrValue utility method.

        Returns state keys for a selected device or the value for a selected
        variable, depending on what is selected in the ``devVarMenu`` control.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary; ``devVarMenu`` key is read.
            type_id: Action type identifier (unused).
            target_id: Target identifier (unused).

        Returns:
            list: List of (state_key, label) tuples for the selected object.
        """
        return self.Fogbert.generatorStateOrValue(values_dict.get('devVarMenu', ""))

    # =============================================================================
    # @staticmethod
    # def generator_substitutions(values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0):  # noqa
    #     """ Placeholder """
    #     return generator_substitutions.return_substitution(values_dict)

    # =============================================================================

    @staticmethod
    def get_serial_ports(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> bool:  # noqa
        """Shim to call the serial_ports.show_ports method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        serial_ports.show_ports(values_dict, no_log)
        return True

    # =============================================================================
    @staticmethod
    def indigo_inventory(no_log: bool = False) -> bool:  # noqa
        """Shim to call the indigo_inventory.show_inventory method.

        Args:
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        indigo_inventory.show_inventory(no_log)
        return True

    # =============================================================================
    @staticmethod
    def inspect_method(values_dict: indigo.Dict = None, type_id: str = "") -> None:  # noqa
        """Shim to call the inspect_method.display_docstring method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
        """
        inspect_method.display_docstring(values_dict)

    # =============================================================================
    @staticmethod
    def installed_plugins(no_log: bool = False) -> bool:
        """Shim to call the installed_plugins.get_list method.

        Args:
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        installed_plugins.get_list(no_log)
        return True

    # =============================================================================
    @staticmethod
    def list_of_plugin_methods(fltr: str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list[tuple[str, str]]:  # noqa
        """Shim to call the plugin_methods.list_methods method.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary passed to the tool.
            target_id: Target identifier (unused).

        Returns:
            list: List of method name tuples for the selected plugin.
        """
        return plugin_methods.list_methods(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_classes(fltr: str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list[tuple[str, str]]:  # noqa
        """Shim to call the indigo_classes.display_classes method.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary passed to the tool.
            target_id: Target identifier (unused).

        Returns:
            list: List of Indigo class name tuples.
        """
        return indigo_classes.display_classes(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_methods(fltr: str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list[tuple[str, str]]:  # noqa
        """Shim to call the indigo_methods.display_methods method.

        Args:
            fltr: Filter string (unused).
            values_dict: Dialog values dictionary passed to the tool.
            target_id: Target identifier (unused).

        Returns:
            list: List of Indigo method name tuples.
        """
        return indigo_methods.display_methods(values_dict)

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict: indigo.Dict = None, type_id: str = "") -> None:  # noqa
        """Shim to call the log_of_method.display_inspection method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
        """
        log_of_method.display_inspection(values_dict)

    # =============================================================================
    @staticmethod
    def lorem_ipsum(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> tuple[bool, indigo.Dict]:  # noqa
        """Shim to call the Lorem Ipsum tool.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            tuple: ``(True, values_dict)``
        """
        lorem_ipsum.report(values_dict)
        return True, values_dict

    @staticmethod
    def modify_numeric_variable(action_group: indigo.actionGroup) -> Any:
        """Shim to call the modify_numeric_variable.modify method.

        Args:
            action_group: Indigo action group containing the target variable ID
                and modifier expression in its props.

        Returns:
            Result of modify_numeric_variable.modify.
        """
        return modify_numeric_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def modify_time_variable(action_group: indigo.actionGroup) -> Any:
        """Shim to call the modify_time_variable.modify method.

        Args:
            action_group: Indigo action group containing the target variable ID
                and time delta values (days, hours, minutes, seconds) in its props.

        Returns:
            Result of modify_time_variable.modify.
        """
        return modify_time_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def network_ping_device_menu(values_dict: indigo.Dict, item_id: str) -> tuple[bool, indigo.Dict]:  # noqa
        """Shim to call the ping_tool.do_the_ping method from a menu item.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            item_id: Menu item identifier (unused by the tool).

        Returns:
            tuple: ``(True, values_dict)``
        """
        ping_tool.do_the_ping(values_dict, menu_call=True)
        return True, values_dict

    # =============================================================================
    def network_ping_device_action(self, action_group: indigo.actionGroup) -> tuple[bool, indigo.actionGroup]:
        """Shim to run the network ping tool from an action and fire any related triggers.

        After pinging, checks whether the updated ping device has a registered
        offline trigger and executes it if the device is offline.

        Args:
            action_group: Indigo action group containing ``selected_device`` in
                its props.

        Returns:
            tuple: ``(True, action_group)``
        """
        # Do the action and process call to update the device
        ping_tool.do_the_ping(action_group, menu_call=False)

        # Process trigger as needed. If the updated device has a trigger configured, it will have a trigger in
        # `self.my_triggers`. It will be {dev.id: <trigger object>}
        dev_id = action_group.props['selected_device']  # the device.id selected in the action config
        if dev_id in self.my_triggers:
            event_id = self.my_triggers[dev_id].id  # the id of the trigger object
            dev = indigo.devices[int(dev_id)]  # the device object
            status = dev.states['status']  # the online status of the ping device

            # if the device is offline, fire the trigger
            if not status:
                indigo.trigger.execute(event_id)

        return True, action_group

    # =============================================================================
    def network_quality_action(self, action_group: indigo.actionGroup) -> None:
        """Shim to run the network quality tool from an action.

        Args:
            action_group: Indigo action group whose props are passed to
                network_quality.
        """
        self.network_quality(action_group.props)

    # =============================================================================
    def network_quality_device_action(self,  action_group: indigo.actionGroup) -> bool:
        """Run the network quality test and update a Network Quality device's states.

        Requires macOS 12.0 or later. Runs ``networkQuality -c`` and parses the
        JSON output to populate device states including throughput, responsiveness,
        base RTT, and timestamps.

        Args:
            action_group: Indigo action group containing ``selected_device``
                and network quality flag props.

        Returns:
            bool: True on success, False if the OS check fails or an error code
            is returned by the networkQuality tool.
        """
        self.logger.info("Running network quality test. The plugin will be unresponsive until the test is complete.")

        if not self.network_quality_test_os():
            return False

        dev = indigo.devices[int(action_group.props['selected_device'])]

        command: list = self.network_quality_flags(dev.pluginProps)  # ['networkQuality', '-u', '-v']
        command.append('-c')  # computer readable format (json) ['networkQuality', '-u', '-v', '-c']
        command = [' '.join(command)]  # ['networkQuality -u -v -c']
        self.logger.debug("Command line args: %s", command)

        # Run the test and get the result.
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        results = json.loads(result)
        self.logger.debug("Results payload: %s", results)

        # The key 'error_code' only exists if there's a problem. For example, NSURLErrorDomain -1009.
        if 'error_code' in results:
            self.logger.warning("Warning: error code %s returned.", results['error_code'])
            return False

        # Calculate the test duration in seconds.
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        start = dt.datetime.strptime(results['end_date'], fmt)
        stop = dt.datetime.strptime(results['start_date'], fmt)
        elapsed_time = (start - stop).total_seconds()
        self.logger.info("Network quality test took approximately %s seconds to complete.", round(elapsed_time, 3))

        # Build the device states list
        states_list = [
            {'key': 'base_rtt', 'value': round(results.get('base_rtt', 0), 3)},
            {'key': 'dl_throughput', 'value': round(results.get('dl_throughput', 0) / 1000000, 3)},
            {'key': 'end_date', 'value': results['end_date']},
            {'key': 'elapsed_time', 'value': round(elapsed_time)},
            {'key': 'responsiveness', 'value': round(results.get('responsiveness', -1), 3)},
            {'key': 'start_date', 'value': results['start_date']},
            {'key': 'ul_throughput', 'value': round(results.get('ul_throughput', 0) / 1000000, 3)},
        ]

        # Update device
        dev.updateStatesOnServer(states_list)

        return True

    def network_quality_test_os(self) -> bool:
        """Test the OS version to ensure the networkQuality tool is available.

        Returns:
            bool: True if macOS 12.0 or later, False otherwise.
        """
        # Test OS compatability
        plat_form = platform.mac_ver()[0].split('.')  # ['14', '4', '1']
        if (float(plat_form[0])) < 12.0:
            self.logger.warning("This tool requires at least MacOS 12.0 Monterey.")
            return False
        return True

    @staticmethod
    def network_quality_flags(props: dict) -> list[str]:
        """Parse plugin props into a networkQuality command-line argument list.

        Args:
            props: Device or action props dict containing boolean flags for
                ``runDownloadTest``, ``runUploadTest``, ``usePrivateRelay``,
                ``runTestsSequentially``, ``verboseOutput``, and
                ``outputVerification``.

        Returns:
            list: Command list starting with ``'networkQuality'`` followed by
            any applicable flags.
        """
        # Build command line argument
        command = ['networkQuality']
        # Do not run a download test (implies -s)
        if not props.get('runDownloadTest', True):
            command.append('-d')
        # Do not run an upload test (implies -s)
        if not props.get('runUploadTest', True):
            command.append('-u')
        # Use iCloud Private Relay.
        if props.get('usePrivateRelay', False):
            command.append('-p')
        # Run tests sequentially instead of parallel upload/download.
        if props.get('runTestsSequentially', False):
            command.append('-s')
        # Verbose output.
        if props.get('verboseOutput', False):
            command.append('-v')
        # Disable verification of the server identity via TLS.
        if props.get('outputVerification', False):
            command.append('-k')

        return command

    # =============================================================================
    def network_quality(self, action_group: indigo.actionGroup, action_id: str = "") -> bool:  # noqa
        """Run the macOS networkQuality tool and log the result asynchronously.

        Builds the command-line arguments from ``action_group`` props and puts
        the command on the background command queue. Output is logged when the
        concurrent thread processes the result queue.

        Args:
            action_group: Action props dict or action group containing network
                quality flag settings.
            action_id: Action identifier (unused).

        Returns:
            bool: True if the OS check passes and the command is queued,
            False otherwise.
        """

        if not self.network_quality_test_os():
            return False

        command = self.network_quality_flags(action_group)
        self.cmd_queue.put(command)
        return True

    # =============================================================================
    @staticmethod
    def pip_freeze_report(values_dict: indigo.Dict = None, type_id: str = "") -> bool:  # noqa
        """Shim to call the pip_freeze.report method.

        Args:
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).

        Returns:
            bool: True on success.
        """
        pip_freeze.report()
        return True

    # =============================================================================
    @staticmethod
    def remove_all_delayed_actions(values_dict: indigo.Dict = None, type_id: str = "") -> bool:  # noqa
        """Shim to call the remove_delayed_actions.remove_actions method.

        Args:
            values_dict: Dialog values dictionary (unused).
            type_id: Action type identifier (unused).

        Returns:
            bool: Result of remove_delayed_actions.remove_actions.
        """
        return remove_delayed_actions.remove_actions()

    # =============================================================================
    def run_concurrent_thread(self) -> None:
        """Standard Indigo concurrent thread; drains the network quality result queue.

        Runs continuously, sleeping one second per iteration. Logs any pending
        network quality results accumulated in ``nq_queue``.
        """
        try:
            while True:
                self.sleep(1)

                # Process any network quality requests.
                while not self.nq_queue.empty():
                    result = self.nq_queue.get()
                    indigo.server.log(f"\n{result}")

        except self.StopThread:
            pass

    # =============================================================================
    @staticmethod
    def running_plugins(no_log: bool = False) -> bool:
        """Shim to call the running_plugins.show_running_plugins method.

        Args:
            no_log: If True, suppresses log output.

        Returns:
            bool: True on success.
        """
        running_plugins.show_running_plugins(no_log)
        return True

    # =============================================================================
    @staticmethod
    def results_output(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> indigo.Dict:
        """Shim to call the results_output.display_results method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            caller: Identifier for the calling context.
            no_log: If True, suppresses log output.

        Returns:
            indigo.Dict: The values dictionary.
        """
        results_output.display_results(values_dict, caller, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def object_directory(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> indigo.Dict:
        """Shim to call the object_directory.display_results method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            caller: Identifier for the calling context.
            no_log: If True, suppresses log output.

        Returns:
            indigo.Dict: The values dictionary.
        """
        object_directory.display_results(values_dict, caller, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def object_dependencies(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> indigo.Dict:  # noqa
        """Shim to call the object_dependencies.display_results method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            caller: Identifier for the calling context.
            no_log: If True, suppresses log output.

        Returns:
            indigo.Dict: The values dictionary.
        """
        object_dependencies.display_results(values_dict, caller, no_log)
        return values_dict

    # =============================================================================
    def search_embedded_scripts(self, values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> Any:  # noqa
        """Shim to call the find_embedded_scripts.make_report method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            Result of find_embedded_scripts.make_report.
        """
        return find_embedded_scripts.make_report(values_dict, no_log)

    # =============================================================================
    def search_linked_scripts(self, values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> Any:  # noqa
        """Shim to call the find_linked_scripts.make_report method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).
            no_log: If True, suppresses log output.

        Returns:
            Result of find_linked_scripts.make_report.
        """
        return find_linked_scripts.make_report(values_dict, no_log)

    # =============================================================================
    @staticmethod
    def send_status_request(values_dict: indigo.Dict = None, type_id: str = "") -> tuple[bool, indigo.Dict]:  # noqa
        """Shim to call the send_status_request.get_status method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).

        Returns:
            tuple: ``(True, result)`` where result is the return value of
            send_status_request.get_status.
        """
        return True, send_status_request.get_status(values_dict)

    # =============================================================================
    @staticmethod
    def speak_string(values_dict: indigo.Dict = None, type_id: str = "") -> Any:  # noqa
        """Shim to call the speak_string.speaker method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).

        Returns:
            Result of speak_string.speaker.
        """
        return speak_string.speaker(values_dict)

    # =============================================================================
    @staticmethod
    def subscribed_to_changes(values_dict: indigo.Dict = None, type_id: str = "") -> Any:  # noqa
        """Shim to call the subscribe_to_changes.subscriber method.

        Args:
            values_dict: Dialog values dictionary passed to the tool.
            type_id: Action type identifier (unused).

        Returns:
            Result of subscribe_to_changes.subscriber.
        """
        return subscribe_to_changes.subscriber(values_dict)

    # =============================================================================
    # @staticmethod
    # def substitution_generator(values_dict: indigo.Dict = None, type_id: str = ""):  # noqa
    #     """ Placeholder """
    #     return substitution_generator.get_substitute(values_dict)

    # =============================================================================
    @staticmethod
    def test_action_return(action: indigo.actionGroup) -> int | float | str | tuple | dict | list | None:
        """Dummy action that returns a typed value for testing plugin.executeAction() callers.

        Acts as a test endpoint for other plugins to verify how they handle
        various return types from executeAction calls.

        Args:
            action: Indigo action object; ``action.props['return_value']`` must
                be one of ``''``, ``None``, ``'int'``, ``'float'``, ``'str'``,
                ``'tuple'``, ``'dict'``, or ``'list'``.

        Returns:
            The value corresponding to the requested return type, or None if the
            type is unrecognized or empty.
        """
        if action.props['return_value'] in [None, ""]:
            return None
        if action.props['return_value'] == "int":
            return 1
        if action.props['return_value'] == "float":
            return 1.0
        if action.props['return_value'] == "str":
            return "string"
        if action.props['return_value'] == "tuple":
            return tuple((None, 1, 2.0, "string", (), indigo.Dict(), indigo.List()))
        if action.props['return_value'] == "dict":
            return {'a': None, 'b': 1, 'c': 2.0, 'd': "string", 'e': (), 'f': indigo.Dict(), 'g': indigo.List()}
        if action.props['return_value'] == "list":
            return [None, 1, 2.0, "string", (), indigo.Dict(), indigo.List()]
        return None

    def my_tests(self, action: indigo.actionGroup | None = None) -> None:  # noqa
        """Run functional tests invoked by the my_test action.

        Executes device creation, action group, and plugin function tests from
        the testPluginCode module. Stops on the first error and logs it to the
        Indigo events log.

        Args:
            action: Indigo action object (unused).
        """
        try:
            from Tests import testPluginCode
            testPluginCode.TestPlugin.test_device_creation(self)
            testPluginCode.TestPlugin.test_action_group_execution(self)
            testPluginCode.TestPlugin.test_plugin_functions(self)

        except Exception as err:
            indigo.server.log(str(err))


# =============================================================================
class MyThread(Thread):
    """Thread subclass for running blocking shell commands in the background.

    Allows long-running commands (e.g. networkQuality) to execute without
    blocking the Indigo UI or keeping dialogs open.
    """
    def __init__(self, target: Callable, args: tuple = ()) -> None:
        """Initialize the thread with a target callable and its arguments.

        Args:
            target: Callable to invoke when the thread runs.
            args: Tuple of positional arguments passed to ``target``.
        """
        super().__init__()
        self.target = target
        self.args = args
        self.stop_event = False
        self.logger = logging.getLogger("Plugin")

    def stop(self) -> None:
        """Signal the thread to stop on its next iteration (e.g. on plugin shutdown)."""
        self.logger.debug("Stopping command thread.")
        self.stop_event = True

    def run(self) -> None:
        """Run the thread, invoking ``target`` repeatedly until stopped."""
        while not self.stop_event:
            if self.target:
                self.target(*self.args)
            else:
                break
