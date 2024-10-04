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
import platform
from queue import Queue
import subprocess
from threading import Thread
from unittest import TestCase
from unittest.mock import MagicMock

import indigo  # noqa
# import pydevd

# My modules
import DLFramework.DLFramework as Dave  # noqa
from constants import DEBUG_LABELS
from plugin_defaults import kDefaultPluginPrefs  # noqa
from Tools import *

# =================================== HEADER ==================================
__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'Multitool Plugin for Indigo Home Control'
__version__   = '2023.2.2'


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

        # ============================= Remote Debugging ==============================
        # try:
        #     pydevd.settrace(port=5678, 'localhost', stdoutToServer=True, stderrToServer=True, suspend=False)
        # except:
        #     pass

    def log_plugin_environment(self):
        """
        Log pluginEnvironment information when plugin is first started
        """
        self.Fogbert.pluginEnvironment()
        return True

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedPrefsConfigUi(self, values_dict: indigo.Dict = None, user_cancelled:bool=False):  # noqa
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

    # =============================================================================
    def deviceUpdated(self, orig_dev:indigo.Device=None, new_dev:indigo.Device=None):  # noqa
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

    @staticmethod
    def get_device_list(filter: str="", type_id: int=0, values_dict: indigo.Dict=None, target_id: int=0) -> list:  # noqa
        return [(dev.id, dev.name) for dev in indigo.devices.iter(filter="self")]

    # =============================================================================
    def getMenuActionConfigUiValues(self, menu_id:str=""):  # noqa
        """
        Title Placeholder

        Body placeholder

        :param str menu_id:
        :return indigo.Dict:
        """
        # Grab the setting values for the "Subscribe to Changes" tool
        if menu_id == 'subscribeToChanges':
            changes_dict = indigo.Dict()
            changes_dict['enableSubscribeToChanges'] = (self.pluginPrefs.get('enableSubscribeToChanges', False))
            changes_dict['subscribedDevices'] = self.pluginPrefs.get('subscribedDevices', '')
            return_value = changes_dict

        else:
            return_value = indigo.Dict()

        return return_value

    # =============================================================================
    @staticmethod
    def sendDevicePing(dev_id:int=0, suppress_logging:bool=False):  # noqa
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
        if self.debug_level == 10:
            self.my_tests()

        # =========================== Audit Indigo Version ============================
        self.Fogbert.audit_server_version(min_ver=2022)

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
        self.command_thread.stop()

    def trigger_start_processing(self, trigger):
        if trigger.id not in self.my_triggers:
            # my_triggers is a dict of triggers with the key being the device the trigger tracks and the value being the
            # trigger object.
            self.my_triggers[trigger.pluginProps['offlineDevice']] = trigger

    # =============================================================================
    def variableUpdated(self, orig_var:indigo.Variable, new_var:indigo.Variable):  # noqa
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
    def validateActionConfigUi(self, action_dict:indigo.Dict=None, type_id:str="", device_id:int=0):  # noqa
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
    def __dummyCallback__(self, values_dict: indigo.Dict = None, type_id: str = ""):
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
    def about_indigo(no_log: bool = False):
        """ Placeholder """
        about_indigo.report(no_log)
        return True

    # =============================================================================
    @staticmethod
    def battery_level_report(values_dict: indigo.Dict = None, type_id:str="", no_log: bool = False):  # noqa
        """ Placeholder """
        battery_level.report(no_log)
        return True

    # =============================================================================
    @staticmethod
    def color_picker(values_dict: indigo.Dict = None, type_id:str="", no_log: bool = False):  # noqa
        """ Placeholder """
        color_picker.picker(values_dict, "", no_log)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def device_inventory(values_dict: indigo.Dict = None, type_id:str="", no_log: bool = False):  # noqa
        """ Placeholder """
        device_inventory.get_inventory(values_dict, type_id, no_log)
        return values_dict

    # =============================================================================
    @staticmethod
    def device_last_successful_comm(values_dict: indigo.Dict = None, menu_item: str = "", no_log: bool = False):
        """ Placeholder """
        device_last_successful_comm.report_comms(values_dict, menu_item, no_log)
        return True

    # =============================================================================
    @staticmethod
    def device_to_beep(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        device_beep.beeper(values_dict)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def device_to_ping(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        device_ping.pinger(values_dict)

    # =============================================================================
    @staticmethod
    def dict_to_print(fltr:str="", values_dict: indigo.Dict = None, target_id:str=""):  # noqa
        """ Placeholder """
        return dict_to_print.print_dict(values_dict)

    # =============================================================================
    @staticmethod
    def environment_path(no_log: bool = False):
        """ Placeholder """
        environment_path.show_path(no_log)
        return True

    # =============================================================================
    @staticmethod
    def error_inventory(values_dict: indigo.Dict = None, type_id:str="", no_log: bool = False):  # noqa
        """ Placeholder """
        error_inventory.show_inventory(values_dict, no_log)
        return True

    # =============================================================================
    def execute_command(self, command_queue, result_queue):
        """ Get command from queue, run it, and capture the output. """
        while True:
            my_command = command_queue.get()
            my_command = ' '.join(my_command)
            if my_command is None:  # None signals the end of command execution
                break
            try:
                # Run command and log result.
                self.logger.debug(f"Command line argument: [ {my_command} ]")
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
    def generator_device_list(self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.deviceList(dev_filter=fltr)

    # =============================================================================
    def generator_variable_list(self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.variableList()

    # =============================================================================
    def generator_enabled_device_list(
            self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0  # noqa
    ):
        """ Placeholder """
        return self.Fogbert.deviceListEnabled(dev_filter=fltr)

    # =============================================================================
    # @staticmethod
    def generator_device_filter(self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        # Built-in filters
        filter_list = [
            ("all devices", "All Devices"),
            ("indigo.controller", "indigo.controller"),
            ("indigo.dimmer", "indigo.dimmer"),
            ("indigo.insteon", "indigo.insteon"),
            ("indigo.iodevice", "indigo.iodevice"),
            ("indigo.relay", "indigo.relay"),
            ("indigo.responder", "indigo.responder"),
            ("indigo.sensor", "indigo.sensor"),
            ("indigo.sprinkler", "indigo.sprinkler"),
            ("indigo.thermostat", "indigo.thermostat"),
            ("indigo.x10", "indigo.x10"),
            ("indigo.zwave", "indigo.zwave"),
        ]

        # Add plugin identifiers
        _ = [filter_list.append((dev.pluginId, dev.pluginId))
             for dev in indigo.devices
             if (dev.pluginId, dev.pluginId) not in filter_list
             ]
        # Remove any duplicate tuples
        unique_tuples = list(set(filter_list))

        # Remove any empty tuples ('', '')
        filter_list = [tup for tup in unique_tuples if (len(tup[0]) + len(tup[1])) > 0]

        return filter_list

    # =============================================================================
    def generator_dev_var(self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_dev_var_clean(self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.deviceAndVariableListClean()

    # =============================================================================
    def generator_state_or_value(self, fltr:str="", values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.generatorStateOrValue(values_dict.get('devVarMenu', ""))

    # =============================================================================
    # @staticmethod
    # def generator_substitutions(values_dict: indigo.Dict = None, type_id:str="", target_id:int=0):  # noqa
    #     """ Placeholder """
    #     return generator_substitutions.return_substitution(values_dict)

    # =============================================================================
    @staticmethod
    def get_serial_ports(values_dict: indigo.Dict = None, type_id:str="", no_log: bool = False):  # noqa
        """ Placeholder """
        serial_ports.show_ports(values_dict, no_log)
        return True

    # =============================================================================
    @staticmethod
    def indigo_inventory(no_log: bool = False):  # noqa
        """ Placeholder """
        indigo_inventory.show_inventory(no_log)
        return True

    # =============================================================================
    @staticmethod
    def inspect_method(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        inspect_method.display_docstring(values_dict)

    # =============================================================================
    @staticmethod
    def installed_plugins(no_log: bool = False):
        """ Placeholder """
        installed_plugins.get_list(no_log)
        return True

    # =============================================================================
    @staticmethod
    def list_of_plugin_methods(fltr:str="", values_dict: indigo.Dict = None, target_id:str=""):  # noqa
        """ Placeholder """
        return plugin_methods.list_methods(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_classes(fltr:str="", values_dict: indigo.Dict = None, target_id:str=""):  # noqa
        """ Placeholder """
        return indigo_classes.display_classes(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_methods(fltr:str="", values_dict: indigo.Dict = None, target_id:str=""):  # noqa
        """ Placeholder """
        return indigo_methods.display_methods(values_dict)

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        log_of_method.display_inspection(values_dict)

    # Apparently Apple removed this functionality in Ventura
    # =============================================================================
    # @staticmethod
    # def man_page(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
    #     """ Placeholder """
    #     return man_page.display_page(values_dict)

    # =============================================================================
    @staticmethod
    def modify_numeric_variable(action_group: indigo.actionGroup):
        """ Placeholder """
        return modify_numeric_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def modify_time_variable(action_group: indigo.actionGroup):
        """ Placeholder """
        return modify_time_variable.modify(action_group)

    # =============================================================================
    def network_ping_device_menu(self, values_dict: indigo.Dict, item_id: str):
        ping_tool.do_the_ping(values_dict, menu_call=True)
        return True, values_dict

    # =============================================================================
    def network_ping_device_action(self, action_group: indigo.actionGroup):
        """ Shim used when running the network ping tool from an action. """
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
    def network_quality_action(self, action_group: indigo.actionGroup):
        """ Shim used when running the network quality tool from an action. """
        self.network_quality(action_group.props)

    # =============================================================================
    def network_quality_device_action(self,  action_group: indigo.actionGroup):
        """ Update network quality device states after running test. """
        self.logger.info("Running network quality test. The plugin will be unresponsive until the test is complete.")

        if not self.network_quality_test_os():
            return False

        dev = indigo.devices[int(action_group.props['selected_device'])]

        command: list = self.network_quality_flags(dev.pluginProps)  # ['networkQuality', '-u', '-v']
        command.append('-c')  # computer readable format (json) ['networkQuality', '-u', '-v', '-c']
        command = [' '.join(command)]  # ['networkQuality -u -v -c']
        self.logger.debug(f"Command line args: {command}")

        # Run the test and get the result.
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        results = json.loads(result)
        self.logger.debug(f"Results payload: {results}")

        # The key 'error_code' only exists if there's a problem. For example, NSURLErrorDomain -1009.
        if 'error_code' in results:
            self.logger.warning(f"Warning: error code {results['error_code']} returned.")
            return False

        # Calculate the test duration in seconds.
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        start = dt.datetime.strptime(results['end_date'], fmt)
        stop = dt.datetime.strptime(results['start_date'], fmt)
        elapsed_time = (start - stop).total_seconds()
        self.logger.info(f"Network quality test took approximately {round(elapsed_time, 3)} seconds to complete.")

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

    def network_quality_test_os(self):
        """ Test the OS version to ensure that the network quality test tool is available """
        # Test OS compatability
        pltfrm = platform.mac_ver()[0].split('.')  # ['14', '4', '1']
        if (float(pltfrm[0])) < 12.0:
            self.logger.warning("This tool requires at least MacOS 12.0 Monterey.")
            return False
        return True

    @staticmethod
    def network_quality_flags(props):
        """ Parse the config preferences into the appropriate command line arguments. """
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
    def network_quality(self, action_group: indigo.actionGroup, action_id: str = ""):
        """ Run the macOS command line Network Quality tool and log the result  """

        if not self.network_quality_test_os():
            return False

        command = self.network_quality_flags(action_group)
        self.cmd_queue.put(command)
        return True

    # =============================================================================
    @staticmethod
    def remove_all_delayed_actions(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        return remove_delayed_actions.remove_actions()

    # =============================================================================
    def run_concurrent_thread(self):
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
    def running_plugins(no_log: bool = False):
        """ Placeholder """
        running_plugins.show_running_plugins(no_log)
        return True

    # =============================================================================
    @staticmethod
    def results_output(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False):
        """ Placeholder """
        results_output.display_results(values_dict, caller, no_log)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def object_directory(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False):
        """ Placeholder """
        object_directory.display_results(values_dict, caller, no_log)
        return True, values_dict

    # =============================================================================
    @staticmethod
    def object_dependencies(values_dict: indigo.Dict = None, caller: str = "", no_log: bool = False):
        """ Placeholder """
        object_dependencies.display_results(values_dict, caller, no_log)
        return True, values_dict

    # =============================================================================
    def search_embedded_scripts(self, values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False):  # noqa
        """ Placeholder """
        return find_embedded_scripts.make_report(values_dict, no_log)

    # =============================================================================
    def search_linked_scripts(self, values_dict: indigo.Dict = None, type_id: str = "", no_log: bool = False):  # noqa
        """ Placeholder """
        return find_linked_scripts.make_report(values_dict, no_log)

    # =============================================================================
    @staticmethod
    def send_status_request(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        return True, send_status_request.get_status(values_dict)

    # =============================================================================
    @staticmethod
    def speak_string(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        return speak_string.speaker(values_dict)

    # =============================================================================
    @staticmethod
    def subscribed_to_changes(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
        """ Placeholder """
        return subscribe_to_changes.subscriber(values_dict)

    # =============================================================================
    # @staticmethod
    # def substitution_generator(values_dict: indigo.Dict = None, type_id:str=""):  # noqa
    #     """ Placeholder """
    #     return substitution_generator.get_substitute(values_dict)

    # =============================================================================
    @staticmethod
    def test_action_return(action, return_value=None):
        """
        Dummy action to test return values

        The test_action_return method is used to test return values for calls to plugin.executeAction() calls. The
        plugin will return a value based on the 'return_value' type passed to the method.
        """
        if action.props['return_value'] in [None, ""]:
            return None
        elif action.props['return_value'] == "int":
            return 1
        elif action.props['return_value'] == "float":
            return 1.0
        elif action.props['return_value'] == "str":
            return "string"
        elif action.props['return_value'] == "tuple":
            return tuple((None, 1, 2.0, "string", (), indigo.Dict(), indigo.List()))
        elif action.props['return_value'] == "dict":
            return {'a': None, 'b': 1, 'c': 2.0, 'd': "string", 'e': (), 'f': indigo.Dict(), 'g': indigo.List()}
        elif action.props['return_value'] == "list":
            return [None, 1, 2.0, "string", (), indigo.Dict(), indigo.List()]

    def test_foobar(self, action):
        """
        This method is used to create and delete a plugin device for unit testing

        The unit test sends a "plugin.executeAction" command message via the IWS API with an instruction to either
        create or delete a plugin device. The action passes the payload through to this method.
        """
        props = action.props
        if props['instruction'] == "create":
            dev = indigo.device.create(
                address=props.get('address', ""),
                configured=props.get('configured', True),
                description=props.get('description', ""),
                deviceTypeId=props.get('deviceTypeId', 'networkQuality'),
                folder=props.get('folder', 0),
                # groupWithDevice=props.get('groupWithDevice', False),  # note GWD is expecting an obj, so we skip for now.
                name=props.get('name', "Unit Test Device"),
                pluginId='com.fogbert.indigoplugin.multitool',
                props=props.get('props', None),
                protocol=indigo.kProtocol.Plugin,
            )
            self.logger.info(f"Unit Test: Created device [{dev.deviceTypeId} - {dev.id}]")
            # TODO: would it be better here to return the entire device obj?
            return {'dev_id': dev.id}  # the id of the device that was created
        if props['instruction'] == "delete":
            indigo.device.delete(props['dev_id'])
            self.logger.info(f"Unit Test: Deleted device [[{props['deviceTypeId']} - {props['dev_id']}]")
            return "dev deleted"

    def my_tests(self):
        """
        The my_tests method runs functional tests every time the plugin is (re)loaded in debug mode.

        If it encounters an error, a message will be written to the Indigo events log. The tests will stop upon the
        first error (subsequent tests will not be run).
        """
        test_case = TestCase()
        self.logger.debug("Running startup tests. (Warning messages are normal.)")
        try:
            # TODO: Add a attribute to suppress log output when relevant methods are called from a test. See
            #     see Indigo Inventory below.
            # ===================================== About Indigo =====================================
            test_case.assertTrue(self.about_indigo(no_log=True), "Method failed.")  # Implied `None` returned
            # ===================================== Battery Level Report =====================================
            test_case.assertTrue(self.battery_level_report(no_log=True), "Method failed.")  # Implied `None` returned
            # ===================================== Color Picker =====================================
            dicts = [
                {'chosenColor': 'FF FF FF'},
                {'chosenColor': 1},  # wrong value type
                {'chosenColor': 'white'}  # wrong value type
            ]
            for test_dict in dicts:
                test_case.assertTrue(self.color_picker(test_dict, no_log=True), "Method failed.")
            # ===================================== Device Beep =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Device Inventory =====================================
            values_dict = {'customThing': 'self', 'typeOfThing': 'Other'}
            test_case.assertIsInstance(self.device_inventory(values_dict, no_log=True), dict, "Method failed.")
            # ===================================== Device Last Comm =====================================
            test_case.assertTrue(self.device_last_successful_comm({'listOfDevices': 'indigo.relay'}, no_log=True), "Method failed.")
            # ===================================== Device Ping =====================================
            # ===================================== Environment Path =====================================
            test_case.assertTrue(self.environment_path(no_log=True), "Method failed")
            # ===================================== Error Inventory =====================================
            for values_dict in [{'error_level': 'err'}, {'error_level': 'err_warn'}]:
                test_case.assertTrue(self.error_inventory(values_dict, no_log=True), "Method failed")
            # ===================================== Indigo Inventory =====================================
            test_case.assertTrue(self.indigo_inventory(no_log=True), "Method failed")
            # ===================================== Methods Indigo Base =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Methods Plugin Base =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Network Quality Report =====================================
            # ===================================== Object Inspection =====================================
            # It's best if the referenced objects are ones that will be around permanently.
            for payload in [{'classOfThing': 'actionGroups', 'thingToPrint': 460267384},
                            {'classOfThing': 'controlPages', 'thingToPrint': 37036932},
                            {'classOfThing': 'devices', 'thingToPrint': 374100038},
                            {'classOfThing': 'schedules', 'thingToPrint': 147884757},
                            {'classOfThing': 'triggers', 'thingToPrint': 1789555909},
                            {'classOfThing': 'variables', 'thingToPrint': 23078783}
                            ]:
                # Print Object Dict
                test_case.assertTrue(self.results_output(payload, no_log=True), "Method failed.")
                # Print Object Dir
                test_case.assertTrue(self.object_directory(payload, no_log=True), "Method failed.")
                # Print Object Dependencies
                test_case.assertTrue(self.object_dependencies(payload, no_log=True), "Method failed.")
            # ===================================== Ping Host =====================================
            # Menu Call
            for hostname in ['10.0.1.1', 'google.com', 'indigo']:
                test_case.assertIsNone(ping_tool.do_the_ping({'hostname': hostname}, menu_call=True), "Method failed.")
            # Action Call
            values_dict = MagicMock()
            values_dict.props = {'selected_device': 1655068310}
            test_case.assertIsInstance(self.network_ping_device_action(values_dict), tuple, "Method failed.")
            # ===================================== Plugin Inventory =====================================
            test_case.assertTrue(self.installed_plugins(no_log=True), "Method failed.")
            # ===================================== Plugins Online =====================================
            test_case.assertTrue(self.running_plugins(no_log=True), "Method failed.")
            # ===================================== Remove Delayed Actions =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Scripts Embedded =====================================
            test_case.assertIsInstance(self.search_embedded_scripts({'search_string': ''}, no_log=True), tuple, "Method failed.")
            test_case.assertTrue(self.search_embedded_scripts({'search_string': ''}, no_log=True)[0], "Method failed.")
            test_case.assertIsInstance(self.search_embedded_scripts({'search_string': 'A'}, no_log=True), tuple, "Method failed.")
            test_case.assertTrue(self.search_embedded_scripts({'search_string': 'A'}, no_log=True)[0], "Method failed.")
            # ===================================== Scripts Linked =====================================
            values_dict = {}
            test_case.assertIsInstance(self.search_linked_scripts(values_dict, no_log=True), tuple, "Method failed.")
            test_case.assertTrue(self.search_linked_scripts(values_dict, no_log=True)[0], "Method failed.")
            # ===================================== Send Status Request =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Serial Ports =====================================
            test_case.assertTrue(self.get_serial_ports({'ignoreBluetooth': True}, no_log=True), "Method failed.")
            # ===================================== Speak String =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Subscribe to Changes =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Display Plugin Information =====================================
            test_case.assertTrue(self.log_plugin_environment(), "Method failed.")
        except AssertionError as err:
            line_number = err.__traceback__.tb_lineno
            indigo.server.log(f"Startup test failed: {err} at line {line_number}", level=logging.ERROR)


# =============================================================================
class MyThread(Thread):
    """
    Subclass of the threading.Thread module for blocking commands.

    The MyThread class is used to subclass the Thread module so that blocking commands can run in the background and
    not block the Indigo UI. This allows select callbacks to fire in while allowing any Indigo dialogs to complete as
    normal (rather than staying open until the command execution is completed).
    """
    def __init__(self, target, args=()):
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
