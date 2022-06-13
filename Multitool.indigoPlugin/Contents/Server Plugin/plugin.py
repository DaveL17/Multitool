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

# Third-party modules
import Tests.test_plugin

try:
    import indigo  # noqa
    import pydevd
except ImportError as error:
    pass

# My modules
import DLFramework.DLFramework as Dave  # noqa
from constants import *  # noqa
from plugin_defaults import kDefaultPluginPrefs  # noqa
from Tools import *
from Tests import *


# =================================== HEADER ==================================
__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'Multitool Plugin for Indigo Home Control'
__version__   = '2022.1.5'


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

        # ============================= Remote Debugging ==============================
        # try:
        #     pydevd.settrace(
        #         port=5678,
        #         'localhost',
        #         stdoutToServer=True,
        #         stderrToServer=True,
        #         suspend=False
        #     )
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
        # Unit Tests
        # indigo.server.log(f"{test_plugin.TestAdd().test_add()}")

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
    @staticmethod
    def about_indigo():
        about_indigo.report()

    # =============================================================================
    def color_picker(self, values_dict=None, type_id=""):  # noqa
        color_picker.picker(values_dict)

    # =============================================================================
    def device_dependencies(self, values_dict=None, type_id=""):  # noqa
        return device_dependencies.dependencies(values_dict)

    # =============================================================================
    def device_inventory(self, values_dict=None, type_id=""):  # noqa
        device_inventory.get_inventory(values_dict, type_id)

    # =============================================================================
    def device_last_successful_comm(self, values_dict, menu_item):
        device_last_successful_comm.report_comms(values_dict, menu_item)

    # =============================================================================
    def device_to_beep(self, values_dict=None, type_id=""):  # noqa
        device_beep.beeper(values_dict)

    # =============================================================================
    def device_to_ping(self, values_dict=None, type_id=""):  # noqa
        device_ping.pinger(values_dict)

    # =============================================================================
    def dict_to_print(self, fltr="", values_dict=None, target_id=""):  # noqa
        return dict_to_print.print_dict(values_dict)

    # =============================================================================
    @staticmethod
    def environment_path():
        environment_path.show_path()

    # =============================================================================
    def error_inventory(self, values_dict=None, type_id=""):  # noqa
        return error_inventory.show_inventory()

    # =============================================================================
    def generator_device_list(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        return self.Fogbert.deviceList(dev_filter=fltr)

    # =============================================================================
    def generator_variable_list(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        return self.Fogbert.variableList()

    # =============================================================================
    def generator_enabled_device_list(
            self, fltr="", values_dict=None, type_id="", target_id=0  # noqa
    ):
        return self.Fogbert.deviceListEnabled(dev_filter=fltr)

    # =============================================================================
    def generator_device_filter(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
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
        [filter_list.append((dev.pluginId, dev.pluginId))
         for dev in indigo.devices
         if (dev.pluginId, dev.pluginId) not in filter_list
         ]

        return filter_list

    # =============================================================================
    def generator_dev_var(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_dev_var_clean(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        return self.Fogbert.deviceAndVariableListClean()

    # =============================================================================
    def generator_state_or_value(self, fltr="", values_dict=None, type_id="", target_id=0):  # noqa
        return self.Fogbert.generatorStateOrValue(values_dict.get('devVarMenu', ""))

    # =============================================================================
    @staticmethod
    def generator_substitutions(values_dict=None, type_id="", target_id=0):  # noqa
        return generator_substitutions.return_substitution(values_dict)

    # =============================================================================
    def get_serial_ports(self, values_dict=None, type_id=""):  # noqa
        return serial_ports.show_ports(values_dict)

    # =============================================================================
    def indigo_inventory(self):  # noqa
        indigo_inventory.show_inventory()

    # =============================================================================
    def inspect_method(self, values_dict=None, type_id=""):  # noqa
        inspect_method.display_docstring(values_dict)

    # =============================================================================
    @staticmethod
    def installed_plugins():
        installed_plugins.get_list()

    # =============================================================================
    def list_of_plugin_methods(self, fltr="", values_dict=None, target_id=""):  # noqa
        return plugin_methods.list_methods(values_dict)

    # =============================================================================
    def list_of_indigo_classes(self, fltr="", values_dict=None, target_id=""):  # noqa
        return indigo_classes.display_classes(values_dict)

    # =============================================================================
    def list_of_indigo_methods(self, fltr="", values_dict=None, target_id=""):  # noqa
        return indigo_methods.display_methods(values_dict)

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict=None, type_id=""):  # noqa
        log_of_method.display_inspection(values_dict)

    # =============================================================================
    def man_page(self, values_dict=None, type_id=""):  # noqa
        return man_page.display_page(values_dict)

    # =============================================================================
    @staticmethod
    def modify_numeric_variable(action_group):
        return modify_numeric_variable.modify(action_group)

    # =============================================================================
    @staticmethod
    def modify_time_variable(action_group):
        return modify_time_variable.modify(action_group)

    # =============================================================================
    def remove_all_delayed_actions(self, values_dict=None, type_id=""):  # noqa
        return remove_delayed_actions.remove_actions()

    # =============================================================================
    @staticmethod
    def running_plugins():
        running_plugins.show_running_plugins()

    # =============================================================================
    @staticmethod
    def results_output(values_dict=None, caller=None):
        results_output.display_results(values_dict, caller)

    # =============================================================================
    @staticmethod
    def object_directory(values_dict=None, caller=None):
        object_directory.display_results(values_dict, caller)

    # =============================================================================
    def send_status_request(self, values_dict=None, type_id=""):  # noqa
        return send_status_request.get_status(values_dict)

    # =============================================================================
    def speak_string(self, values_dict=None, type_id=""):  # noqa
        return speak_string.speaker(values_dict)

    # =============================================================================
    def subscribed_to_changes(self, values_dict=None, type_id=""):  # noqa
        return subscribe_to_changes.subscriber(values_dict)

    # =============================================================================
    def substitution_generator(self, values_dict=None, type_id=""):  # noqa
        return substitution_generator.get_substitute(values_dict)

    # =============================================================================
    @staticmethod
    def add(a, b):
        """ This is a placeholdeer method to start constructing unit tests """
        return a + b
