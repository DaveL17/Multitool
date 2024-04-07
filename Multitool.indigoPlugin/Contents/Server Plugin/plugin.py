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

try:
    import indigo  # noqa
    # import pydevd
except ImportError as error:
    pass

# My modules
import DLFramework.DLFramework as Dave  # noqa
from constants import DEBUG_LABELS
from plugin_defaults import kDefaultPluginPrefs  # noqa
from Tools import *
# from Tests import *

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
        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False

        # =============================== Debug Logging ================================
        self.debug_level = int(self.pluginPrefs.get('showDebugLevel', '30'))
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

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedPrefsConfigUi(self, values_dict:indigo.Dict=None, user_cancelled:bool=False):  # noqa
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
        # Run unit Tests
        # test_plugin.Tester().run_tests()

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
    def about_indigo():
        """ Placeholder """
        about_indigo.report()

    # =============================================================================
    @staticmethod
    def battery_level_report(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        battery_level.report(values_dict)

    # =============================================================================
    @staticmethod
    def color_picker(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        color_picker.picker(values_dict)
        return True

    # =============================================================================
    @staticmethod
    def device_inventory(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        device_inventory.get_inventory(values_dict, type_id)

    # =============================================================================
    @staticmethod
    def device_last_successful_comm(values_dict: indigo.Dict = None, menu_item: str = ""):
        """ Placeholder """
        device_last_successful_comm.report_comms(values_dict, menu_item)

    # =============================================================================
    @staticmethod
    def device_to_beep(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        device_beep.beeper(values_dict)

    # =============================================================================
    @staticmethod
    def device_to_ping(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        device_ping.pinger(values_dict)

    # =============================================================================
    @staticmethod
    def dict_to_print(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return dict_to_print.print_dict(values_dict)

    # =============================================================================
    @staticmethod
    def environment_path():
        """ Placeholder """
        environment_path.show_path()

    # =============================================================================
    @staticmethod
    def error_inventory(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return error_inventory.show_inventory(values_dict)

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
    def generator_device_list(self, fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.deviceList(dev_filter=fltr)

    # =============================================================================
    def generator_variable_list(self, fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.variableList()

    # =============================================================================
    def generator_enabled_device_list(
            self, fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0  # noqa
    ):
        """ Placeholder """
        return self.Fogbert.deviceListEnabled(dev_filter=fltr)

    # =============================================================================
    @staticmethod
    def generator_device_filter(fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
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

        return filter_list

    # =============================================================================
    def generator_dev_var(self, fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_dev_var_clean(self, fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.deviceAndVariableListClean()

    # =============================================================================
    def generator_state_or_value(self, fltr:str="", values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return self.Fogbert.generatorStateOrValue(values_dict.get('devVarMenu', ""))

    # =============================================================================
    @staticmethod
    def generator_substitutions(values_dict:indigo.Dict=None, type_id:str="", target_id:int=0):  # noqa
        """ Placeholder """
        return generator_substitutions.return_substitution(values_dict)

    # =============================================================================
    @staticmethod
    def get_serial_ports(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return serial_ports.show_ports(values_dict)

    # =============================================================================
    @staticmethod
    def indigo_inventory():  # noqa
        """ Placeholder """
        indigo_inventory.show_inventory()

    # =============================================================================
    @staticmethod
    def inspect_method(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        inspect_method.display_docstring(values_dict)

    # =============================================================================
    @staticmethod
    def installed_plugins():
        """ Placeholder """
        installed_plugins.get_list()

    # =============================================================================
    @staticmethod
    def list_of_plugin_methods(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return plugin_methods.list_methods(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_classes(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return indigo_classes.display_classes(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_methods(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return indigo_methods.display_methods(values_dict)

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        log_of_method.display_inspection(values_dict)

    # Apparently Apple removed this functionality in Ventura
    # =============================================================================
    # @staticmethod
    # def man_page(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
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
    def remove_all_delayed_actions(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
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
    def running_plugins():
        """ Placeholder """
        running_plugins.show_running_plugins()

    # =============================================================================
    @staticmethod
    def results_output(values_dict: indigo.Dict = None, caller: str = ""):
        """ Placeholder """
        results_output.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def object_directory(values_dict: indigo.Dict = None, caller: str = ""):
        """ Placeholder """
        object_directory.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def object_dependencies(values_dict: indigo.Dict = None, caller: str = ""):
        """ Placeholder """
        object_dependencies.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def send_status_request(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return send_status_request.get_status(values_dict)

    # =============================================================================
    @staticmethod
    def speak_string(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return speak_string.speaker(values_dict)

    # =============================================================================
    @staticmethod
    def subscribed_to_changes(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return subscribe_to_changes.subscriber(values_dict)

    # =============================================================================
    @staticmethod
    def substitution_generator(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return substitution_generator.get_substitute(values_dict)

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
