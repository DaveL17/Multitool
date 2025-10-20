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
import subprocess
from threading import Thread
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
__version__   = '2025.1.3'


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
        """
        Log pluginEnvironment information when plugin is first started
        """
        self.Fogbert.pluginEnvironment()
        return True

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedPrefsConfigUi(self, values_dict: indigo.Dict = None, user_cancelled: bool = False) -> dict:  # noqa
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
            indigo.server.log(f"Debugging on (Level: {DEBUG_LABELS[self.debug_level]} ({self.debug_level})")
            self.logger.debug("Plugin prefs saved.")

        else:
            self.logger.debug("Plugin prefs cancelled.")

        return values_dict

    @staticmethod
    def get_attrib_dict(orig_obj, new_obj, exclude: tuple) -> dict:
        """ Return a dictionary of attributes where the new object has the attributes removed."""
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
    def deviceUpdated(self, orig_dev: indigo.Device = None, new_dev: indigo.Device = None):  # noqa
        """
        Standard Indigo method called when device is updated.

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
    def get_device_list(filter: str="", type_id: int=0, values_dict: indigo.Dict=None, target_id: int=0) -> list:  # noqa
        """PLACEHOLDER"""
        return [(dev.id, dev.name) for dev in indigo.devices.iter(filter="self")]

    # =============================================================================
    def getMenuActionConfigUiValues(self, menu_id: str = "") -> dict:  # noqa
        """
        Standard Indigo method called when a config menu is opened.

        :param str menu_id:
        :return indigo.Dict:
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
    def sendDevicePing(dev_id: int = 0, suppress_logging: bool = False) -> dict:  # noqa
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
        Standard Indigo startup method.

        :return:
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
    def shutdown(self):
        """ Standed Indigo shutdown method."""
        self.command_thread.stop()

    def trigger_start_processing(self, trigger: indigo.Trigger):
        """
        Standard Indigo method called when a trigger starts processing.

        :param indigo.Trigger trigger: a dict of triggers with the key being the device the trigger tracks and the
        value being the trigger object.
        """
        if trigger.id not in self.my_triggers:
            self.my_triggers[trigger.pluginProps['offlineDevice']] = trigger

    # =============================================================================
    def variableUpdated(self, orig_var: indigo.Variable, new_var: indigo.Variable) -> None:  # noqa
        """
        Standard Indigo method called when a variable is updated.

        :param indigo.Variable orig_var:
        :param indigo.Variable new_var:
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
    def validateActionConfigUi(self, action_dict: indigo.Dict = None, type_id: str = "", device_id: int = 0) -> tuple:  # noqa
        """
        Standard method called to validate action config dialogs.

        :param indigo.Dict action_dict:
        :param int type_id:
        :param int device_id:
        :return:
        """
        error_msg_dict = indigo.Dict()

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
        """
        Dummy callback to cause refresh of dialog elements

        The __dummyCallback__ method is used and a placeholder callback to force a refresh of
        dialog elements based for controls with dynamic refresh attributes.

        :param indigo.Dict values_dict:
        :param int type_id:
        :return:
        """

    # =============================================================================
    @staticmethod
    def about_indigo(no_log: bool = False) -> bool:
        """
        Shim to call the About Indigo tool.

        :param bool no_log: If True, no output is logged.
        """
        about_indigo.report(no_log)
        return True

    # =============================================================================
    @staticmethod
    def battery_level_report(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False):  # noqa
        """
        SHim to call the Battery level report tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool no_log: If True, no output is logged.
        """
        battery_level.report(no_log)
        return True

    # =============================================================================
    @staticmethod
    def color_picker(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> tuple[bool, dict]:  # noqa
        """
        Shim to call the ColorPicker tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool no_log: If True, no output is logged.
        """
        color_picker.picker(values_dict, "", no_log)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def device_inventory(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> dict:  # noqa
        """
        Shim to call the DeviceInventory tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool no_log: If True, no output is logged.
        """
        device_inventory.get_inventory(values_dict, type_id, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def device_last_successful_comm(values_dict: indigo.Dict = None, menu_item: str = "", no_log: bool = False):
        """
        Shim to call the Device_last_successful_comm tool.

        :param indigo.Dict values_dict:
        :param str menu_item:
        :param bool no_log: If True, no output is logged.
        """
        device_last_successful_comm.report_comms(values_dict, menu_item, no_log)

    # =============================================================================
    @staticmethod
    def device_to_beep(values_dict: indigo.Dict = None, type_id: str = "") -> tuple[bool, dict]:  # noqa
        """
        Shim to call the Device_to_beep tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        """
        device_beep.beeper(values_dict)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def device_to_ping(values_dict: indigo.Dict = None, type_id: str = "") -> None:  # noqa
        """
        Shim to call the Device_to_ping tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        """
        device_ping.pinger(values_dict)

    # =============================================================================
    @staticmethod
    def dict_to_print(fltr:str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list:  # noqa
        """
        Shim to call the dict_to_print tool.

        :param indigo.Dict values_dict:
        :param str target_id:
        """
        return dict_to_print.print_dict(values_dict)

    # =============================================================================
    @staticmethod
    def environment_path(no_log: bool = False) -> bool:
        """
        Shim to call the environment_path tool.

        :param bool no_log: If True, no output is logged.
        """
        environment_path.show_path(no_log)
        return True

    # =============================================================================
    @staticmethod
    def error_inventory(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> bool:  # noqa
        """
        Shim to call the error_inventory tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool no_log: If True, no output is logged.
        """
        error_inventory.show_inventory(values_dict, no_log)
        return True

    # =============================================================================
    def execute_command(self, command_queue: Queue, result_queue: Queue) -> None:
        """
        Get command from queue, run it, and capture the output.

        :param Queue command_queue:
        :param Queue result_queue:
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
    def generator_device_list(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        Shim to call the Fogbert.deviceList utility method.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
        """
        return self.Fogbert.deviceList(dev_filter=fltr)

    # =============================================================================
    def generator_variable_list(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        SHim to call the Fogbert.variableList utility method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
        """
        return self.Fogbert.variableList()

    # =============================================================================
    def generator_enabled_device_list(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        Shim to call the deviceListEnabled utility method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
        """
        return self.Fogbert.deviceListEnabled(dev_filter=fltr)

    # =============================================================================
    # @staticmethod
    def generator_device_filter(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        Build a list of device filters

        Will include all the standard Indigo filters (indigo.relay, indigo.sensor, etc.) and plugin IDs.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
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
    def generator_dev_var(self, fltr: str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        Shim to call the Fogbert.deviceAndVariableList utility method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
        """
        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_dev_var_clean(self, fltr:str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        Shim to call the Fogbert.deviceAndVariableList utility method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
        """
        return self.Fogbert.deviceAndVariableListClean()

    # =============================================================================
    def generator_state_or_value(self, fltr:str = "", values_dict: indigo.Dict = None, type_id: str = "", target_id: int = 0) -> list:  # noqa
        """
        Shim to call the Fogbert.generatorStateOrValue utility method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool target_id:
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
        """
        Shim to call the serial_ports.show_ports method.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool no_log: If True, no output is logged.
        """
        serial_ports.show_ports(values_dict, no_log)
        return True

    # =============================================================================
    @staticmethod
    def indigo_inventory(no_log: bool = False) -> bool:  # noqa
        """
        Shim to call the indigo_inventory.show_inventory method.

        :param bool no_log: If True, no output is logged.
        """
        indigo_inventory.show_inventory(no_log)
        return True

    # =============================================================================
    @staticmethod
    def inspect_method(values_dict: indigo.Dict = None, type_id: str = "") -> None:  # noqa
        """
        Shim to call the inspect_method.display_docstring method.

        :param indigo.Dict values_dict:
        :param str type_id:
        """
        inspect_method.display_docstring(values_dict)

    # =============================================================================
    @staticmethod
    def installed_plugins(no_log: bool = False) -> bool:
        """
        Shim to call the installed_plugins.get_list method.

        :param bool no_log: If True, no output is logged.
        """
        installed_plugins.get_list(no_log)
        return True

    # =============================================================================
    @staticmethod
    def list_of_plugin_methods(fltr: str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list:  # noqa
        """
        Shim to call the plugin_methods.list_methods method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str target_id:
        """
        return plugin_methods.list_methods(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_classes(fltr:str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list:  # noqa
        """
        Shim to call the indigo_classes.display_classes method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str target_id:
        """
        return indigo_classes.display_classes(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_methods(fltr: str = "", values_dict: indigo.Dict = None, target_id: str = "") -> list:  # noqa
        """
        Shim to call the indigo_methods.display_methods method.

        :param str fltr:
        :param indigo.Dict values_dict:
        :param str target_id:
        """
        return indigo_methods.display_methods(values_dict)

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict: indigo.Dict = None, type_id: str = "") -> None:  # noqa
        """
        Shim to call the log_of_method.display_inspection method.

        :param indigo.Dict values_dict:
        :param str type_id:
        """
        log_of_method.display_inspection(values_dict)

    # =============================================================================
    @staticmethod
    def lorem_ipsum(values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False) -> tuple[bool, dict]:  # noqa
        """
        Shim to call the lorem ipsum tool.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param bool no_log: If True, no output is logged.
        """
        lorem_ipsum.report(values_dict)
        return True, values_dict

    @staticmethod
    def modify_numeric_variable(action_group: indigo.actionGroup):
        """
        Shim to call the modify_numeric_variable.modify method.

        :param action_group:
        """
        return modify_numeric_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def modify_time_variable(action_group: indigo.actionGroup):
        """
        Shim to call the modify_time_variable.modify method.

        :param action_group:
        """
        return modify_time_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def network_ping_device_menu(values_dict: indigo.Dict, item_id: str) -> tuple[bool, dict]:  # noqa
        """
        Shim to call the ping_tool.do_the_ping method.

        :param indigo.Dict values_dict:
        :param str item_id:
        """
        ping_tool.do_the_ping(values_dict, menu_call=True)
        return True, values_dict

    # =============================================================================
    def network_ping_device_action(self, action_group: indigo.actionGroup) -> tuple[bool, dict]:
        """
        Shim used when running the network ping tool from an action.

        :param action_group:
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
        """
        Shim used when running the network quality tool from an action.

        :param action_group:
        """
        self.network_quality(action_group.props)

    # =============================================================================
    def network_quality_device_action(self,  action_group: indigo.actionGroup) -> bool:
        """
        Update network quality device states after running test.

        :param action_group:
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
        """ Test the OS version to ensure that the network quality test tool is available """
        # Test OS compatability
        plat_form = platform.mac_ver()[0].split('.')  # ['14', '4', '1']
        if (float(plat_form[0])) < 12.0:
            self.logger.warning("This tool requires at least MacOS 12.0 Monterey.")
            return False
        return True

    @staticmethod
    def network_quality_flags(props) -> list:
        """
        Parse the config preferences into the appropriate command line arguments.

        :param dict props:
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
        """
        Run the macOS command line Network Quality tool and log the result

        :param indigo.actionGroup action_group:
        :param str action_id:
        """

        if not self.network_quality_test_os():
            return False

        command = self.network_quality_flags(action_group)
        self.cmd_queue.put(command)
        return True

    # =============================================================================
    @staticmethod
    def remove_all_delayed_actions(values_dict: indigo.Dict = None, type_id: str = "") -> bool:  # noqa
        """
        Shim to call the remove_delayed_actions.remove_actions method.

        :param dict values_dict:
        :param type_id:
        """
        return remove_delayed_actions.remove_actions()

    # =============================================================================
    def run_concurrent_thread(self):
        """PLACEHOLDER"""
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
        """
        Shim to call the running_plugins.show_running_plugins method.

        :param bool no_log: If True, no output is logged.
        """
        running_plugins.show_running_plugins(no_log)
        return True

    # =============================================================================
    @staticmethod
    def results_output(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> tuple[bool, dict]:
        """
        Shim to call the results_output.display_results method.

        :param dict values_dict:
        :param caller:
        :param bool no_log: If True, no output is logged.
        """
        results_output.display_results(values_dict, caller, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def object_directory(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> tuple[bool, dict]:
        """
        Shim to call the object_directory.display_results method.

        :param dict values_dict:
        :param caller:
        :param bool no_log: If True, no output is logged.
        """
        object_directory.display_results(values_dict, caller, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def object_dependencies(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False) -> tuple[bool, dict]:  # noqa
        """
        Shim to call the object_dependencies.display_results method.

        :param dict values_dict:
        :param caller:
        :param bool no_log: If True, no output is logged.
        """
        object_dependencies.display_results(values_dict, caller, no_log)
        return values_dict

    # =============================================================================
    def search_embedded_scripts(self, values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False):  # noqa
        """
        Shim to call the find_embedded_scripts.make_report method.

        :param dict values_dict:
        :param type_id:
        :param bool no_log: If True, no output is logged.
        """
        return find_embedded_scripts.make_report(values_dict, no_log)

    # =============================================================================
    def search_linked_scripts(self, values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False):  # noqa
        """
        Shim to call the find_linked_scripts.make_report method.

        :param dict values_dict:
        :param type_id:
        :param bool no_log: If True, no output is logged.
        """
        return find_linked_scripts.make_report(values_dict, no_log)

    # =============================================================================
    @staticmethod
    def send_status_request(values_dict: indigo.Dict = None, type_id: str = "") -> tuple:  # noqa
        """
        Shim to call the send_status_request.send_status method.

        :param dict values_dict:
        :param type_id:
        """
        return True, send_status_request.get_status(values_dict)

    # =============================================================================
    @staticmethod
    def speak_string(values_dict: indigo.Dict = None, type_id: str = ""):  # noqa
        """
        Shim to call the speak_string.speaker method.

        :param dict values_dict:
        :param type_id:
        """
        return speak_string.speaker(values_dict)

    # =============================================================================
    @staticmethod
    def subscribed_to_changes(values_dict: indigo.Dict = None, type_id: str = ""):  # noqa
        """
        Shim to call the subscribe_to_changes.subscriber method.

        :param dict values_dict:
        :param type_id:
        """
        return subscribe_to_changes.subscriber(values_dict)

    # =============================================================================
    # @staticmethod
    # def substitution_generator(values_dict: indigo.Dict = None, type_id: str = ""):  # noqa
    #     """ Placeholder """
    #     return substitution_generator.get_substitute(values_dict)

    # =============================================================================
    @staticmethod
    def test_action_return(action):
        """
        Dummy action to test return values

        The test_action_return method is used to test return values for calls to plugin.executeAction() calls. It is an
        endpoint to be called when testing other code bases. The Multitool plugin will return a value based on the
        'return_value' type passed to the method.

        :param action:
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

    def my_tests(self, action=None):  # noqa
        """
        The my_tests method runs functional tests that are invoked by calling the my_test action.

        If it encounters an error, a message will be written to the Indigo events log. The tests will stop upon the
        first error (subsequent tests will not be run).
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
    """
    Subclass of the threading.Thread module for blocking commands.

    The MyThread class is used to subclass the Thread module so that blocking commands can run in the background and
    not block the Indigo UI. This allows select callbacks to fire in while allowing any Indigo dialogs to complete as
    normal (rather than staying open until the command execution is completed).
    """
    def __init__(self, target, args=()):
        """
        Placeholder

        :param target:
        :param args:
        """
        super().__init__()
        self.target = target
        self.args = args
        self.stop_event = False
        self.logger = logging.getLogger("Plugin")

    def stop(self):
        """ Stop the thread when the stop event is called (like plugin shutdown/reload). """
        self.logger.debug("Stopping command thread.")
        self.stop_event = True

    def run(self):
        """ Run the thread. """
        while not self.stop_event:
            if self.target:
                self.target(*self.args)
            else:
                break
