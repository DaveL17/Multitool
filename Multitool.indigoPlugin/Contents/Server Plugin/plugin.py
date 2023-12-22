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
import logging

try:
    import indigo  # noqa
    # import pydevd
except ImportError as error:
    pass

# My modules
import DLFramework.DLFramework as Dave  # noqa
from constants import DEBUG_LABELS
from plugin_defaults import kDefaultPluginPrefs  # noqa
import Tools
# from Tests import *


# =================================== HEADER ==================================
__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'Multitool Plugin for Indigo Home Control'
__version__   = '2023.1.0'


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
        log_format = '%(asctime)s.%(msecs)03d\t%(levelname)-10s\t%(name)s.%(funcName)-28s %(message)s'
        self.debug_level = int(self.pluginPrefs.get('showDebugLevel', '30'))
        self.plugin_file_handler.setFormatter(
            logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        )
        self.indigo_log_handler.setLevel(self.debug_level)

        # ====================== Initialize DLFramework =======================
        self.Fogbert = Dave.Fogbert(self)
        self.Eval    = Dave.evalExpr(self)

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
            indigo.server.log(
                f"Debugging on (Level: {DEBUG_LABELS[self.debug_level]} ({self.debug_level})"
            )

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
            changes_dict['enableSubscribeToChanges'] = (
                self.pluginPrefs.get('enableSubscribeToChanges', False)
            )
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
                error_msg_dict['list_of_variables'] = (
                    "The variable value must be a POSIX timestamp."
                )

            for val in ('days', 'hours', 'minutes', 'seconds'):
                try:
                    float(self.substitute(action_dict[val]))
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
    def __dummyCallback__(self, values_dict:indigo.Dict=None, type_id:str=""):
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
        Tools.about_indigo.report()

    # =============================================================================
    @staticmethod
    def battery_level_report(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.battery_level.report(values_dict)

    # =============================================================================
    @staticmethod
    def color_picker(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.color_picker.picker(values_dict)
        return True

    # =============================================================================
    # def device_dependencies(self, values_dict:indigo.Dict=None, type_id:str=""):  # noqa fixme
    #     return device_dependencies.dependencies(values_dict)

    # =============================================================================
    @staticmethod
    def device_inventory(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.device_inventory.get_inventory(values_dict, type_id)

    # =============================================================================
    @staticmethod
    def device_last_successful_comm(values_dict:indigo.Dict=None, menu_item:str=""):
        """ Placeholder """
        Tools.device_last_successful_comm.report_comms(values_dict, menu_item)

    # =============================================================================
    @staticmethod
    def device_to_beep(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.device_beep.beeper(values_dict)

    # =============================================================================
    @staticmethod
    def device_to_ping(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.device_ping.pinger(values_dict)

    # =============================================================================
    @staticmethod
    def dict_to_print(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return Tools.dict_to_print.print_dict(values_dict)

    # =============================================================================
    @staticmethod
    def environment_path():
        """ Placeholder """
        Tools.environment_path.show_path()

    # =============================================================================
    @staticmethod
    def error_inventory(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.error_inventory.show_inventory(values_dict)

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
        return Tools.generator_substitutions.return_substitution(values_dict)

    # =============================================================================
    @staticmethod
    def get_serial_ports(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.serial_ports.show_ports(values_dict)

    # =============================================================================
    @staticmethod
    def indigo_inventory():  # noqa
        """ Placeholder """
        Tools.indigo_inventory.show_inventory()

    # =============================================================================
    @staticmethod
    def inspect_method(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.inspect_method.display_docstring(values_dict)

    # =============================================================================
    @staticmethod
    def installed_plugins():
        """ Placeholder """
        Tools.installed_plugins.get_list()

    # =============================================================================
    @staticmethod
    def list_of_plugin_methods(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return Tools.plugin_methods.list_methods(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_classes(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return Tools.indigo_classes.display_classes(values_dict)

    # =============================================================================
    @staticmethod
    def list_of_indigo_methods(fltr:str="", values_dict:indigo.Dict=None, target_id:str=""):  # noqa
        """ Placeholder """
        return Tools.indigo_methods.display_methods(values_dict)

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        Tools.log_of_method.display_inspection(values_dict)

    # =============================================================================
    @staticmethod
    def man_page(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.man_page.display_page(values_dict)

    # =============================================================================
    @staticmethod
    def modify_numeric_variable(action_group:indigo.actionGroup):
        """ Placeholder """
        return Tools.modify_numeric_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def modify_time_variable(action_group:indigo.actionGroup):
        """ Placeholder """
        return Tools.modify_time_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def remove_all_delayed_actions(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.remove_delayed_actions.remove_actions()

    # =============================================================================
    @staticmethod
    def running_plugins():
        """ Placeholder """
        Tools.running_plugins.show_running_plugins()

    # =============================================================================
    @staticmethod
    def results_output(values_dict:indigo.Dict=None, caller:str=""):
        """ Placeholder """
        Tools.results_output.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def object_directory(values_dict:indigo.Dict=None, caller:str=""):
        """ Placeholder """
        Tools.object_directory.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def object_dependencies(values_dict:indigo.Dict=None, caller:str=""):
        """ Placeholder """
        Tools.object_dependencies.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def send_status_request(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.send_status_request.get_status(values_dict)

    # =============================================================================
    @staticmethod
    def speak_string(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.speak_string.speaker(values_dict)

    # =============================================================================
    @staticmethod
    def subscribed_to_changes(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.subscribe_to_changes.subscriber(values_dict)

    # =============================================================================
    @staticmethod
    def substitution_generator(values_dict:indigo.Dict=None, type_id:str=""):  # noqa
        """ Placeholder """
        return Tools.substitution_generator.get_substitute(values_dict)

    # =============================================================================
    @staticmethod
    def add(a, b):
        """ This is a placeholder method to start constructing unit tests """
        return a + b
